#!/usr/bin/env python3
"""Fetch CurseForge mod files and publish Renovate-compatible registry JSON."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API_BASE = "https://api.curseforge.com/v1"
MINECRAFT_GAME_ID = 432
MODPACK_CLASS_ID = 4471

MOD_LOADER_TYPES = {
    "any": 0,
    "forge": 1,
    "cauldron": 2,
    "liteloader": 3,
    "fabric": 4,
    "quilt": 5,
    "neoforge": 6,
}

PROJECT_TYPE_PATHS = {
    "mod": "mc-mods",
    "modpack": "modpacks",
}


def api_request(path: str, api_key: str) -> dict:
    request = urllib.request.Request(
        f"{API_BASE}{path}",
        headers={
            "x-api-key": api_key,
            "Accept": "application/json",
            "User-Agent": "ClarisseGilles-curseforge-registry/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def search_mod(slug: str, project_type: str, api_key: str) -> dict:
    params = {
        "gameId": str(MINECRAFT_GAME_ID),
        "slug": slug,
    }
    if project_type == "modpack":
        params["classId"] = str(MODPACK_CLASS_ID)

    query = urllib.parse.urlencode(params)
    payload = api_request(f"/mods/search?{query}", api_key)
    mods = payload.get("data") or []
    if not mods:
        raise LookupError(f"No CurseForge project found for slug '{slug}' ({project_type})")
    return mods[0]


def version_matches_prefix(game_versions: list[str], prefix: str) -> bool:
    normalized_prefix = prefix.rstrip(".")
    for version in game_versions:
        if version == normalized_prefix or version.startswith(f"{normalized_prefix}."):
            return True
    return False


def loader_matches(file_loaders: list[dict], mod_loader: str) -> bool:
    if not mod_loader:
        return True

    expected = mod_loader.lower()
    for loader in file_loaders:
        loader_type = str(loader.get("type", "")).lower()
        if loader_type == expected:
            return True
    return False


def fetch_matching_files(
    mod_id: int,
    mod_loader: str,
    game_version_prefix: str,
    api_key: str,
) -> list[dict]:
    loader_type = MOD_LOADER_TYPES.get(mod_loader.lower(), 0)
    params = {
        "pageSize": "50",
        "index": "0",
    }
    if loader_type:
        params["modLoaderType"] = str(loader_type)

    query = urllib.parse.urlencode(params)
    payload = api_request(f"/mods/{mod_id}/files?{query}", api_key)
    files = payload.get("data") or []

    matching = []
    for file_info in files:
        game_versions = file_info.get("gameVersions") or []
        file_loaders = file_info.get("modLoaders") or []
        if not version_matches_prefix(game_versions, game_version_prefix):
            continue
        if mod_loader and not loader_matches(file_loaders, mod_loader):
            continue
        matching.append(file_info)

    matching.sort(key=lambda item: item.get("fileDate", ""), reverse=True)
    return matching


def build_release(file_info: dict, slug: str, project_type: str) -> dict:
    file_id = str(file_info["id"])
    path_segment = PROJECT_TYPE_PATHS[project_type]
    changelog_url = (
        f"https://www.curseforge.com/minecraft/{path_segment}/{slug}/files/{file_id}"
    )
    release = {
        "version": file_id,
        "releaseTimestamp": file_info.get("fileDate"),
        "changelogUrl": changelog_url,
        "displayName": file_info.get("displayName"),
        "fileName": file_info.get("fileName"),
        "gameVersions": file_info.get("gameVersions") or [],
        "modLoaders": [
            loader.get("type")
            for loader in (file_info.get("modLoaders") or [])
            if loader.get("type")
        ],
    }
    if file_info.get("isAlternate"):
        release["isStable"] = False
    return release


def build_registry_entry(mod_config: dict, mod_info: dict, latest_file: dict) -> dict:
    slug = mod_config["slug"]
    project_type = mod_config["projectType"]
    path_segment = PROJECT_TYPE_PATHS[project_type]
    package_name = mod_config["packageName"]

    return {
        "packageName": package_name,
        "mod": {
            "id": mod_info["id"],
            "slug": slug,
            "name": mod_info.get("name"),
            "projectType": project_type,
            "modLoader": mod_config.get("modLoader"),
            "gameVersion": mod_config.get("gameVersion"),
        },
        "homepage": f"https://www.curseforge.com/minecraft/{path_segment}/{slug}",
        "registryUrl": f"{mod_config['_base_url']}/{package_name}.json",
        "updatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "releases": [build_release(latest_file, slug, project_type)],
    }


def write_registry_file(registry_dir: Path, package_name: str, payload: dict) -> Path:
    output_path = registry_dir / f"{package_name}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return output_path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    registry_dir = repo_root / "registry"
    config_path = registry_dir / "config.json"

    api_key = os.environ.get("CURSEFORGE_API_KEY", "").strip()
    if not api_key:
        print("CURSEFORGE_API_KEY is required", file=sys.stderr)
        return 1

    config = json.loads(config_path.read_text(encoding="utf-8"))
    base_url = config.get("baseUrl", "https://clarissegilles.github.io/registry").rstrip("/")
    mods = config.get("mods") or []

    index_entries = []
    for mod_config in mods:
        package_name = mod_config["packageName"]
        mod_config = {**mod_config, "_base_url": base_url}
        print(f"Updating {package_name}...")

        mod_info = search_mod(
            slug=mod_config["slug"],
            project_type=mod_config["projectType"],
            api_key=api_key,
        )
        matching_files = fetch_matching_files(
            mod_id=mod_info["id"],
            mod_loader=mod_config.get("modLoader", ""),
            game_version_prefix=mod_config.get("gameVersion", ""),
            api_key=api_key,
        )
        if not matching_files:
            raise LookupError(
                f"No files found for {package_name} "
                f"({mod_config.get('modLoader')} {mod_config.get('gameVersion')})"
            )

        payload = build_registry_entry(mod_config, mod_info, matching_files[0])
        write_registry_file(registry_dir, package_name, payload)
        index_entries.append(
            {
                "packageName": package_name,
                "slug": mod_config["slug"],
                "name": mod_info.get("name"),
                "projectType": mod_config["projectType"],
                "modLoader": mod_config.get("modLoader"),
                "gameVersion": mod_config.get("gameVersion"),
                "latestVersion": payload["releases"][0]["version"],
                "registryUrl": payload["registryUrl"],
                "updatedAt": payload["updatedAt"],
            }
        )
        print(f"  latest file id: {payload['releases'][0]['version']}")

    index_payload = {
        "description": "CurseForge mod registry for Renovate custom datasources",
        "baseUrl": base_url,
        "updatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "mods": index_entries,
    }
    index_path = registry_dir / "index.json"
    index_path.write_text(json.dumps(index_payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(index_entries)} registry files and {index_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        print(f"HTTP {error.code} from CurseForge API: {body}", file=sys.stderr)
        raise SystemExit(1) from error
