#!/usr/bin/env python3
"""
Kiểm tra và cập nhật skills từ upstream repositories.

Chức năng:
- Đọc tất cả skill.yaml trong thư mục skills/
- Fetch commit hash mới nhất từ GitHub API cho mỗi upstream
- So sánh với commit hash hiện tại (lưu trong .upstream_version)
- Nếu có thay đổi: cập nhật metadata, tạo changelog, commit
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml
import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
VERSION_FILE = REPO_ROOT / ".upstream_versions.json"
GITHUB_API = "https://api.github.com/repos"


def get_latest_commit(owner: str, repo: str, branch: str = "main") -> dict | None:
    url = f"{GITHUB_API}/{owner}/{repo}/commits/{branch}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "pascai-skill-updater/1.0",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = httpx.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return {
            "sha": data["sha"],
            "message": data["commit"]["message"].split("\n")[0],
            "date": data["commit"]["committer"]["date"],
            "url": data["html_url"],
        }
    except Exception as e:
        print(f"  [WARN] Không thể fetch {owner}/{repo}: {e}")
        return None


def parse_github_url(url: str) -> tuple[str, str] | None:
    patterns = [
        r"github\.com[:/]([^/]+)/([^/.]+)(?:\.git)?",
        r"github\.com/([^/]+)/([^/\s]+)",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1), m.group(2)
    return None


def load_versions() -> dict:
    if VERSION_FILE.exists():
        return json.loads(VERSION_FILE.read_text(encoding="utf-8"))
    return {}


def save_versions(versions: dict) -> None:
    VERSION_FILE.write_text(
        json.dumps(versions, indent=2, default=str), encoding="utf-8"
    )


def update_skill_yaml(skill_dir: Path, new_sha: str) -> bool:
    yaml_path = skill_dir / "skill.yaml"
    if not yaml_path.exists():
        return False

    content = yaml_path.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    if not data or "skill" not in data:
        return False

    skill = data["skill"]
    if "upstream" not in skill:
        return False

    old_sha = skill["upstream"].get("commit_hash", "")
    if old_sha == new_sha:
        return False

    skill["upstream"]["commit_hash"] = new_sha
    skill["upstream"]["last_sync"] = datetime.now(timezone.utc).isoformat()

    yaml_path.write_text(
        yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return True


def main():
    print("=" * 60)
    print("pascai-skill: Check upstream updates")
    print("=" * 60)

    versions = load_versions()
    updates_found = []
    now = datetime.now(timezone.utc).isoformat()

    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue

        yaml_path = skill_dir / "skill.yaml"
        if not yaml_path.exists():
            continue

        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        if not data or "skill" not in data:
            continue

        skill = data["skill"]
        skill_id = skill.get("id", skill_dir.name)
        upstream = skill.get("upstream")
        if not upstream:
            continue

        url = upstream.get("url", "")
        branch = upstream.get("branch", "main")
        parsed = parse_github_url(url)

        if not parsed:
            print(f"\n  [{skill_id}] Skip (not GitHub): {url}")
            continue

        owner, repo = parsed
        old_sha = versions.get(skill_id, {}).get("commit_hash", upstream.get("commit_hash", ""))
        print(f"\n  [{skill_id}] {owner}/{repo} ({branch})")

        result = get_latest_commit(owner, repo, branch)
        if not result:
            versions[skill_id] = versions.get(skill_id, {})
            versions[skill_id]["last_check"] = now
            versions[skill_id]["error"] = "Failed to fetch"
            save_versions(versions)
            continue

        new_sha = result["sha"][:7]
        print(f"    Current: {old_sha[:7] if old_sha else 'N/A'}")
        print(f"    Latest:  {new_sha}")

        if old_sha and old_sha.startswith(new_sha):
            print(f"    -> Up-to-date")
            versions[skill_id] = {
                "commit_hash": result["sha"],
                "short_hash": new_sha,
                "message": result["message"],
                "date": result["date"],
                "url": result["url"],
                "last_check": now,
                "status": "up-to-date",
            }
            save_versions(versions)
            continue

        updated = update_skill_yaml(skill_dir, result["sha"])
        if updated:
            print(f"    -> UPDATED: {new_sha}")
            updates_found.append({
                "skill_id": skill_id,
                "old_sha": old_sha[:7] if old_sha else "N/A",
                "new_sha": new_sha,
                "message": result["message"],
                "url": result["url"],
            })
        else:
            print(f"    -> First check")

        versions[skill_id] = {
            "commit_hash": result["sha"],
            "short_hash": new_sha,
            "message": result["message"],
            "date": result["date"],
            "url": result["url"],
            "last_check": now,
            "status": "updated" if updated else "first-check",
        }
        save_versions(versions)

    print("\n" + "=" * 60)
    if updates_found:
        print(f"Found {len(updates_found)} updates:")
        for u in updates_found:
            print(f"  * {u['skill_id']}: {u['old_sha']} -> {u['new_sha']}")
            print(f"    {u['message']}")

        changelog = generate_changelog(updates_found)
        changelog_path = REPO_ROOT / "CHANGELOG_UPSTREAM.md"
        existing = ""
        if changelog_path.exists():
            existing = changelog_path.read_text(encoding="utf-8") + "\n\n"
        changelog_path.write_text(existing + changelog, encoding="utf-8")
        print(f"\nChangelog: {changelog_path}")
    else:
        print("No new updates.")

    print("=" * 60)
    return len(updates_found)


def generate_changelog(updates: list) -> str:
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"## Update {date}", ""]
    for u in updates:
        lines.append(f"- **{u['skill_id']}**: {u['old_sha']} -> `{u['new_sha']}`")
        lines.append(f"  {u['message']}")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    count = main()
    sys.exit(0 if count == 0 else 0)  # Always exit 0 for CI
