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

MOD_LOADER_TYPE_NAMES = {value: name for name, value in MOD_LOADER_TYPES.items()}

PROJECT_TYPE_PATHS = {
    "mod": "mc-mods",
    "modpack": "modpacks",
}

CHANGELOG_PLACEHOLDERS = (
    "_Changelog will be populated by the CurseForge registry updater._",
    "_No changelog provided on CurseForge._",
)


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


def mod_loader_type_id(mod_loader: str) -> int:
    return MOD_LOADER_TYPES.get(mod_loader.lower(), 0)


def loader_type_label(loader_type: object) -> str:
    if isinstance(loader_type, int):
        return MOD_LOADER_TYPE_NAMES.get(loader_type, str(loader_type))
    return str(loader_type)


def loader_type_matches(loader_type: object, mod_loader: str) -> bool:
    expected_id = mod_loader_type_id(mod_loader)
    if expected_id == 0:
        return True
    if isinstance(loader_type, int):
        return loader_type == expected_id
    normalized = str(loader_type).lower()
    return normalized == mod_loader.lower() or normalized == MOD_LOADER_TYPE_NAMES.get(expected_id, "")


def search_mod(
    slug: str,
    project_type: str,
    api_key: str,
    *,
    game_version: str = "",
    mod_loader: str = "",
) -> dict:
    params = {
        "gameId": str(MINECRAFT_GAME_ID),
        "slug": slug,
    }
    if project_type == "modpack":
        params["classId"] = str(MODPACK_CLASS_ID)
    if game_version:
        params["gameVersion"] = game_version
    loader_type = mod_loader_type_id(mod_loader)
    if loader_type:
        params["modLoaderType"] = str(loader_type)

    query = urllib.parse.urlencode(params)
    payload = api_request(f"/mods/search?{query}", api_key)
    mods = payload.get("data") or []
    if not mods:
        raise LookupError(f"No CurseForge project found for slug '{slug}' ({project_type})")
    return mods[0]


def fetch_mod_file(mod_id: int, file_id: int, api_key: str) -> dict:
    payload = api_request(f"/mods/{mod_id}/files/{file_id}", api_key)
    file_info = payload.get("data")
    if not file_info:
        raise LookupError(f"CurseForge file {file_id} was not found for mod {mod_id}")
    return file_info


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


def file_game_versions(file_info: dict) -> list[str]:
    versions = list(file_info.get("gameVersions") or [])
    for entry in file_info.get("sortableGameVersions") or []:
        version = entry.get("gameVersion") or entry.get("gameVersionName")
        if version and version not in versions:
            versions.append(version)
    return versions


def file_loader_types(file_info: dict) -> list[object]:
    return [loader.get("type") for loader in (file_info.get("modLoaders") or []) if loader.get("type") is not None]


def file_has_loader_metadata(file_info: dict, mod_loader: str) -> bool:
    return any(loader_type_matches(loader_type, mod_loader) for loader_type in file_loader_types(file_info))


def file_matches_loader_selection(
    file_info: dict,
    mod_loader: str,
    *,
    trust_loader_filter: bool,
) -> bool:
    loaders = file_loader_types(file_info)
    if loaders:
        return file_has_loader_metadata(file_info, mod_loader)
    return trust_loader_filter


def fetch_mod_files(mod_id: int, params: dict[str, str], api_key: str) -> list[dict]:
    query = urllib.parse.urlencode(params)
    payload = api_request(f"/mods/{mod_id}/files?{query}", api_key)
    return payload.get("data") or []


def newest_matching_version(files: list[dict], game_version_prefix: str) -> list[dict]:
    matching = [
        file_info
        for file_info in files
        if version_matches_prefix(file_game_versions(file_info), game_version_prefix)
    ]
    matching.sort(key=lambda item: item.get("fileDate", ""), reverse=True)
    return matching


def describe_resolution_context(
    mod_info: dict,
    mod_loader: str,
    game_version_prefix: str,
    api_key: str,
) -> str:
    lines = []
    for index in mod_info.get("latestFilesIndexes") or []:
        lines.append(
            "- index: "
            f"fileId={index.get('fileId')} "
            f"gameVersion={index.get('gameVersion')} "
            f"modLoader={loader_type_label(index.get('modLoader'))}"
        )

    loader_type = mod_loader_type_id(mod_loader)
    if loader_type:
        params: dict[str, str] = {
            "modLoaderType": str(loader_type),
            "pageSize": "5",
            "index": "0",
        }
        if game_version_prefix:
            params["gameVersion"] = game_version_prefix
        for file_info in fetch_mod_files(mod_info["id"], params, api_key):
            loader_labels = [loader_type_label(value) for value in file_loader_types(file_info)]
            lines.append(
                f"- api: {file_info.get('id')}: "
                f"{file_info.get('displayName')} "
                f"({file_info.get('fileName')}) "
                f"versions={file_game_versions(file_info)} "
                f"loaders={loader_labels or ['(none listed)']}"
            )

    return "\n".join(lines) if lines else "(no loader-specific CurseForge entries found)"


def resolve_file_id_from_indexes(
    mod_info: dict,
    mod_loader: str,
    game_version_prefix: str,
) -> int | None:
    for index in mod_info.get("latestFilesIndexes") or []:
        index_version = index.get("gameVersion", "")
        if not version_matches_prefix([index_version], game_version_prefix):
            continue
        if loader_type_matches(index.get("modLoader"), mod_loader):
            file_id = index.get("fileId")
            if file_id is not None:
                return int(file_id)
    return None


def fetch_loader_filtered_files(
    mod_id: int,
    mod_loader: str,
    game_version_prefix: str,
    api_key: str,
) -> list[dict]:
    loader_type = mod_loader_type_id(mod_loader)
    if not loader_type:
        return []

    def accept_loader_filtered(files: list[dict]) -> list[dict]:
        compatible = [
            file_info
            for file_info in files
            if file_matches_loader_selection(
                file_info,
                mod_loader,
                trust_loader_filter=True,
            )
        ]
        compatible.sort(key=lambda item: item.get("fileDate", ""), reverse=True)
        return compatible

    if game_version_prefix:
        files = fetch_mod_files(
            mod_id,
            {
                "modLoaderType": str(loader_type),
                "gameVersion": game_version_prefix,
                "pageSize": "50",
                "index": "0",
            },
            api_key,
        )
        compatible = accept_loader_filtered(files)
        if compatible:
            return compatible

    files = fetch_mod_files(
        mod_id,
        {
            "modLoaderType": str(loader_type),
            "pageSize": "50",
            "index": "0",
        },
        api_key,
    )
    return accept_loader_filtered(newest_matching_version(files, game_version_prefix))


def resolve_latest_file(
    mod_info: dict,
    mod_loader: str,
    game_version_prefix: str,
    api_key: str,
) -> dict:
    mod_id = mod_info["id"]

    file_id = resolve_file_id_from_indexes(mod_info, mod_loader, game_version_prefix)
    if file_id is not None:
        file_info = fetch_mod_file(mod_id, file_id, api_key)
        if version_matches_prefix(file_game_versions(file_info), game_version_prefix) and file_matches_loader_selection(
            file_info,
            mod_loader,
            trust_loader_filter=True,
        ):
            return file_info

    loader_filtered_files = fetch_loader_filtered_files(
        mod_id,
        mod_loader,
        game_version_prefix,
        api_key,
    )
    if loader_filtered_files:
        return loader_filtered_files[0]

    for file_info in mod_info.get("latestFiles") or []:
        if not version_matches_prefix(file_game_versions(file_info), game_version_prefix):
            continue
        if file_has_loader_metadata(file_info, mod_loader):
            return file_info

    hint = describe_resolution_context(mod_info, mod_loader, game_version_prefix, api_key)
    raise LookupError(
        f"No {mod_loader} {game_version_prefix} file found for mod {mod_id}.\n"
        f"CurseForge loader-specific entries:\n{hint}"
    )


def remove_placeholder_sections(content: str) -> str:
    if not content.strip():
        return content

    placeholder_pattern = "|".join(re.escape(marker) for marker in CHANGELOG_PLACEHOLDERS)
    cleaned = re.sub(
        rf"(?ms)^##\s+[^\n]+\n+(?:{placeholder_pattern})\s*\n+",
        "",
        content,
    )
    return cleaned.strip() + "\n" if cleaned.strip() else ""


def upsert_changelog_section(
    existing_content: str,
    version: str,
    display_name: str,
    body: str,
) -> str:
    existing_content = remove_placeholder_sections(existing_content)
    section_header = f"## {version}"
    section_body = body.strip()
    section_lines = [f"# {display_name}", "", section_header]
    if section_body:
        section_lines.extend(["", section_body, ""])
    else:
        section_lines.append("")

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


def finalize_changelog_content(content: str) -> str:
    cleaned = remove_placeholder_sections(content)
    return cleaned if cleaned.endswith("\n") or not cleaned else cleaned + "\n"


def build_release(
    file_info: dict,
    slug: str,
    project_type: str,
    curseforge_changelog_url: str,
) -> dict:
    release = {
        "version": str(file_info["id"]),
        "releaseTimestamp": file_info.get("fileDate"),
        "changelogUrl": curseforge_changelog_url,
        "displayName": file_info.get("displayName"),
        "fileName": file_info.get("fileName"),
        "gameVersions": file_info.get("gameVersions") or [],
        "modLoaders": [loader_type_label(value) for value in file_loader_types(file_info)],
    }
    if file_info.get("isAlternate"):
        release["isStable"] = False
    return release


def release_sort_key(release: dict) -> int:
    try:
        return int(release["version"])
    except (KeyError, TypeError, ValueError):
        return 0


def parse_changelog_versions(changelog_content: str) -> list[str]:
    return re.findall(r"^##\s+(\S+)\s*$", changelog_content, re.MULTILINE)


def ensure_minimum_release_history(
    releases: list[dict],
    latest_file: dict,
    mod_info: dict,
    mod_config: dict,
    api_key: str,
) -> list[dict]:
    """Renovate needs at least two registry releases to embed changelog dropdowns."""
    if len(releases) >= 2:
        return releases

    loader_files = fetch_loader_filtered_files(
        mod_info["id"],
        mod_config.get("modLoader", ""),
        mod_config.get("gameVersion", ""),
        api_key,
    )
    latest_id = str(latest_file["id"])
    path_segment = PROJECT_TYPE_PATHS[mod_config["projectType"]]
    slug = mod_config["slug"]

    for file_info in loader_files:
        file_id = str(file_info["id"])
        if file_id == latest_id:
            continue
        changelog_url = (
            f"https://www.curseforge.com/minecraft/{path_segment}/{slug}/files/{file_id}"
        )
        previous_release = build_release(file_info, slug, mod_config["projectType"], changelog_url)
        return merge_releases(releases, previous_release)

    return releases


def merge_releases(existing_releases: list[dict], latest_release: dict) -> list[dict]:
    by_version = {str(release["version"]): release for release in existing_releases}
    by_version[str(latest_release["version"])] = latest_release
    return sorted(by_version.values(), key=release_sort_key, reverse=True)


def ensure_release_entries(
    releases: list[dict],
    versions: list[str],
    mod_id: int,
    slug: str,
    project_type: str,
    api_key: str,
) -> list[dict]:
    path_segment = PROJECT_TYPE_PATHS[project_type]
    by_version = {str(release["version"]): release for release in releases}
    for version in versions:
        if version in by_version:
            continue
        changelog_url = (
            f"https://www.curseforge.com/minecraft/{path_segment}/{slug}/files/{version}"
        )
        try:
            file_info = fetch_mod_file(mod_id, int(version), api_key)
            by_version[version] = build_release(file_info, slug, project_type, changelog_url)
        except LookupError:
            by_version[version] = {
                "version": version,
                "changelogUrl": changelog_url,
            }
    return sorted(by_version.values(), key=release_sort_key, reverse=True)


def build_registry_entry(
    mod_config: dict,
    mod_info: dict,
    releases: list[dict],
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
        "releases": releases,
    }


def write_registry_file(registry_dir: Path, package: str, payload: dict) -> Path:
    output_path = registry_dir / f"{package}.json"
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
            game_version=mod_config.get("gameVersion", ""),
            mod_loader=mod_config.get("modLoader", ""),
        )
        latest_file = resolve_latest_file(
            mod_info,
            mod_loader=mod_config.get("modLoader", ""),
            game_version_prefix=mod_config.get("gameVersion", ""),
            api_key=api_key,
        )

        file_id = int(latest_file["id"])
        changelog_body = fetch_changelog(mod_info["id"], file_id, api_key)

        changelog_path = repo_root / changelog_dir / "CHANGELOG.md"
        changelog_path.parent.mkdir(parents=True, exist_ok=True)
        existing_changelog = (
            changelog_path.read_text(encoding="utf-8") if changelog_path.exists() else ""
        )
        display_name = (
            f"{mod_info.get('name')} ({mod_config['modLoader']} {mod_config['gameVersion']})"
        )
        changelog_path.write_text(
            finalize_changelog_content(
                upsert_changelog_section(
                    existing_changelog,
                    str(file_id),
                    display_name,
                    changelog_body,
                )
            ),
            encoding="utf-8",
        )

        path_segment = PROJECT_TYPE_PATHS[mod_config["projectType"]]
        latest_release = build_release(
            latest_file,
            mod_config["slug"],
            mod_config["projectType"],
            f"https://www.curseforge.com/minecraft/{path_segment}/{mod_config['slug']}/files/{latest_file['id']}",
        )

        registry_path = registry_dir / f"{package}.json"
        existing_releases: list[dict] = []
        if registry_path.exists():
            existing_payload = json.loads(registry_path.read_text(encoding="utf-8"))
            existing_releases = existing_payload.get("releases") or []

        changelog_versions = parse_changelog_versions(
            changelog_path.read_text(encoding="utf-8")
        )
        releases = merge_releases(existing_releases, latest_release)
        releases = ensure_minimum_release_history(
            releases,
            latest_file,
            mod_info,
            mod_config,
            api_key,
        )
        releases = ensure_release_entries(
            releases,
            changelog_versions,
            mod_info["id"],
            mod_config["slug"],
            mod_config["projectType"],
            api_key,
        )

        payload = build_registry_entry(
            mod_config,
            mod_info,
            releases,
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
                "latestVersion": releases[0]["version"],
                "registryUrl": payload["registryUrl"],
                "changelogUrl": payload["changelogUrl"],
                "sourceDirectory": changelog_dir,
                "updatedAt": payload["updatedAt"],
            }
        )
        print(
            f"  latest file id: {payload['releases'][0]['version']} "
            f"({latest_file.get('fileName')})"
        )

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
