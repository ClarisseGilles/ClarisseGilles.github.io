#!/usr/bin/env python3
"""Fetch CurseForge mod files and publish Renovate-compatible registry JSON."""

from __future__ import annotations

import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
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


class HTMLToText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"p", "br", "div", "li", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"p", "div", "li", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")


def html_to_markdown(text: str) -> str:
    parser = HTMLToText()
    parser.feed(text)
    normalized = "\n".join(line.rstrip() for line in "".join(parser.parts).splitlines())
    normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip()
    return normalized


def package_name(game_version: str, mod_loader: str, slug: str) -> str:
    return f"{game_version}/{mod_loader.lower()}/{slug}"


def changelog_directory(game_version: str, mod_loader: str, slug: str) -> str:
    return f"changelogs/{package_name(game_version, mod_loader, slug)}"


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


def fetch_changelog(mod_id: int, file_id: int, api_key: str) -> str:
    payload = api_request(f"/mods/{mod_id}/files/{file_id}/changelog", api_key)
    raw_html = payload.get("data") or ""
    if not raw_html:
        return ""
    return html_to_markdown(html.unescape(raw_html))


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


def upsert_changelog_section(
    existing_content: str,
    version: str,
    display_name: str,
    body: str,
) -> str:
    section_header = f"## {version}"
    section_lines = [
        f"# {display_name}",
        "",
        section_header,
        "",
        body.strip() if body.strip() else "_No changelog provided on CurseForge._",
        "",
    ]

    if not existing_content.strip():
        return "\n".join(section_lines).strip() + "\n"

    pattern = re.compile(rf"^##\s+{re.escape(version)}\s*$", re.MULTILINE)
    if pattern.search(existing_content):
        return re.sub(
            rf"(?ms)^##\s+{re.escape(version)}\s*\n.*?(?=^##\s+|\Z)",
            "\n".join(section_lines[2:]).strip() + "\n\n",
            existing_content,
        ).strip() + "\n"

    title_match = re.match(r"^#\s+.+", existing_content)
    if title_match:
        updated = (
            existing_content[: title_match.end()]
            + "\n\n"
            + "\n".join(section_lines[2:]).strip()
            + "\n"
            + existing_content[title_match.end() :].lstrip()
        )
        return updated.strip() + "\n"

    return ("\n".join(section_lines).strip() + "\n\n" + existing_content.strip()).strip() + "\n"


def build_release(
    file_info: dict,
    slug: str,
    project_type: str,
    curseforge_changelog_url: str,
) -> dict:
    file_id = str(file_info["id"])
    path_segment = PROJECT_TYPE_PATHS[project_type]
    release = {
        "version": file_id,
        "releaseTimestamp": file_info.get("fileDate"),
        "changelogUrl": curseforge_changelog_url,
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


def build_registry_entry(
    mod_config: dict,
    mod_info: dict,
    latest_file: dict,
    source_url: str,
    changelog_dir: str,
    changelog_markdown_url: str,
) -> dict:
    slug = mod_config["slug"]
    project_type = mod_config["projectType"]
    path_segment = PROJECT_TYPE_PATHS[project_type]
    package = mod_config["packageName"]

    return {
        "packageName": package,
        "mod": {
            "id": mod_info["id"],
            "slug": slug,
            "name": mod_info.get("name"),
            "projectType": project_type,
            "modLoader": mod_config.get("modLoader"),
            "gameVersion": mod_config.get("gameVersion"),
        },
        "homepage": f"https://www.curseforge.com/minecraft/{path_segment}/{slug}",
        "registryUrl": f"{mod_config['_base_url']}/{package}.json",
        "sourceUrl": source_url,
        "sourceDirectory": changelog_dir,
        "changelogUrl": changelog_markdown_url,
        "updatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "releases": [
            build_release(
                latest_file,
                slug,
                project_type,
                f"https://www.curseforge.com/minecraft/{path_segment}/{slug}/files/{latest_file['id']}",
            )
        ],
    }


def write_registry_file(registry_dir: Path, package: str, payload: dict) -> Path:
    output_path = registry_dir / f"{package}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return output_path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    registry_dir = repo_root / "registry"
    changelogs_dir = repo_root / "changelogs"
    config_path = registry_dir / "config.json"

    api_key = os.environ.get("CURSEFORGE_API_KEY", "").strip()
    if not api_key:
        print("CURSEFORGE_API_KEY is required", file=sys.stderr)
        return 1

    config = json.loads(config_path.read_text(encoding="utf-8"))
    base_url = config.get("baseUrl", "https://clarissegilles.github.io/registry").rstrip("/")
    source_url = config.get(
        "sourceUrl",
        "https://github.com/ClarisseGilles/ClarisseGilles.github.io",
    )
    mods = config.get("mods") or []

    index_entries = []
    for mod in mods:
        mod_config = {
            **mod,
            "packageName": package_name(
                mod["gameVersion"],
                mod["modLoader"],
                mod["slug"],
            ),
            "_base_url": base_url,
        }
        package = mod_config["packageName"]
        changelog_dir = changelog_directory(
            mod["gameVersion"],
            mod["modLoader"],
            mod["slug"],
        )
        changelog_markdown_url = (
            f"{base_url.replace('/registry', '')}/{changelog_dir}/CHANGELOG.md"
        )

        print(f"Updating {package}...")

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
                f"No files found for {package} "
                f"({mod_config.get('modLoader')} {mod_config.get('gameVersion')})"
            )

        latest_file = matching_files[0]
        file_id = int(latest_file["id"])
        changelog_body = fetch_changelog(mod_info["id"], file_id, api_key)

        changelog_path = changelogs_dir / changelog_dir / "CHANGELOG.md"
        changelog_path.parent.mkdir(parents=True, exist_ok=True)
        existing_changelog = (
            changelog_path.read_text(encoding="utf-8") if changelog_path.exists() else ""
        )
        display_name = (
            f"{mod_info.get('name')} ({mod_config['modLoader']} {mod_config['gameVersion']})"
        )
        changelog_path.write_text(
            upsert_changelog_section(
                existing_changelog,
                str(file_id),
                display_name,
                changelog_body,
            ),
            encoding="utf-8",
        )

        payload = build_registry_entry(
            mod_config,
            mod_info,
            latest_file,
            source_url,
            changelog_dir,
            changelog_markdown_url,
        )
        write_registry_file(registry_dir, package, payload)
        index_entries.append(
            {
                "packageName": package,
                "slug": mod_config["slug"],
                "name": mod_info.get("name"),
                "projectType": mod_config["projectType"],
                "modLoader": mod_config.get("modLoader"),
                "gameVersion": mod_config.get("gameVersion"),
                "latestVersion": payload["releases"][0]["version"],
                "registryUrl": payload["registryUrl"],
                "changelogUrl": payload["changelogUrl"],
                "sourceDirectory": changelog_dir,
                "updatedAt": payload["updatedAt"],
            }
        )
        print(f"  latest file id: {payload['releases'][0]['version']}")

    index_payload = {
        "description": "CurseForge mod registry for Renovate custom datasources",
        "baseUrl": base_url,
        "sourceUrl": source_url,
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
