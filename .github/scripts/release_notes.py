#!/usr/bin/env python3
"""Susun changelog rilis Avenia + deteksi rilis duplikat.

Dipakai oleh job `release` di .github/workflows/build-kernel.yml.

Yang dilakukan:
  1. Bandingkan sha256 zip baru dengan checksums.txt pada rilis terakhir.
     Jika identik (tidak ada perubahan biner) → set output duplicate=true,
     rilis baru tidak dibuat (kecuali --force 1).
  2. Susun changelog lengkap: perubahan upstream (kernel/fork/scripts/AK3,
     dengan judul commit dari GitHub Compare API), perubahan repo sejak tag
     rilis sebelumnya, identitas kernel (SUSFS/KernelSU/clang), patch stack
     + sha256, status sinkronisasi DroidSpaces, dan checksum.
  3. Tulis release-notes.md (body rilis) + changelog-section.md (untuk CHANGELOG.md).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.github.com"
COMPONENT_REPOS = {
    "kernel": "Reinazhard/guacamole_sickness",
    "ksu": "Reinazhard/KernelSU",
    "scripts": "Reinazhard/scripts",
    "ak3": "Reinazhard/AnyKernel3",
}
COMPONENT_LABELS = {
    "kernel": "Kernel tree (`guacamole_sickness`)",
    "ksu": "Driver KernelSU (`KernelSU@fork`)",
    "scripts": "Skrip build (`scripts`)",
    "ak3": "Pembungkus flash (`AnyKernel3`)",
}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # noqa: D401
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def api(url: str, token: str, raw: bool = False):
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "avenia-changelog",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read()
            return body if raw else json.loads(body or b"null")
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        print(f"::warning::API gagal ({url}): {exc}", file=sys.stderr)
        return None


def download_asset(asset: dict, token: str) -> bytes | None:
    """Unduh asset rilis: 302 → Location, lalu fetch TANPA header auth."""
    url = asset.get("url", "")
    try:
        OPENER.open(
            urllib.request.Request(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/octet-stream",
                },
            ),
            timeout=60,
        )
    except urllib.error.HTTPError as exc:
        location = exc.headers.get("Location")
        if not location:
            return None
        with urllib.request.urlopen(location, timeout=120) as resp:
            return resp.read()
    except urllib.error.URLError:
        return None
    return None


def git(*args: str, default: str = "") -> str:
    try:
        return subprocess.check_output(["git", *args], text=True).strip()
    except subprocess.CalledProcessError:
        return default


def short(sha: str) -> str:
    return (sha or "")[:8] or "—"


def upstream_changes(old_state: dict, new_state: dict, token: str) -> tuple[list[str], list[str]]:
    """Kembalikan (baris markdown tabel ringkasan, blok detail perubahan)."""
    table = [
        "| Komponen | Sebelumnya | Sekarang | Status |",
        "|---|---|---|---|",
    ]
    details: list[str] = []
    old_comp = (old_state or {}).get("components", {})
    new_comp = new_state.get("components", {})

    for key, label in COMPONENT_LABELS.items():
        old_sha = (old_comp.get(key) or {}).get("sha", "")
        new_sha = (new_comp.get(key) or {}).get("sha", "")
        if not old_sha:
            status = "baseline"
        elif old_sha == new_sha:
            status = "tetap"
        else:
            status = "**berubah**"
        table.append(f"| {label} | `{short(old_sha)}` | `{short(new_sha)}` | {status} |")

        if old_sha and new_sha and old_sha != new_sha:
            slug = COMPONENT_REPOS[key]
            cmp_data = api(f"{API}/repos/{slug}/compare/{old_sha}...{new_sha}", token)
            details.append(f"### {label}")
            details.append("")
            details.append(f"`{short(old_sha)}` → `{short(new_sha)}` — [diff]({slug}/compare/{old_sha}...{new_sha})")
            details.append("")
            commits = (cmp_data or {}).get("commits", []) or []
            if commits:
                for commit in commits[:25]:
                    msg = (commit.get("commit", {}).get("message") or "").splitlines()
                    subject = msg[0] if msg else "(tanpa pesan)"
                    details.append(f"- `{commit.get('sha', '')[:8]}` {subject}")
                if len(commits) > 25:
                    details.append(f"- … dan {len(commits) - 25} commit lainnya")
            else:
                details.append("- (rincian commit tidak tersedia — cek tautan diff di atas)")
            details.append("")
    return table, details


def repo_changes(prev_tag: str) -> list[str]:
    ignore_bot = ["--invert-grep", "--grep=^changelog:"]
    if prev_tag:
        raw = git(
            "log", "--no-merges", "--date=short", *ignore_bot,
            "--pretty=- `%h` %s _(%ad)_", f"{prev_tag}..HEAD",
        )
        if not raw:
            return ["- Tidak ada perubahan pada repo CI sejak rilis sebelumnya."]
        lines = raw.splitlines()
        if len(lines) > 40:
            lines = lines[:40] + [f"- … dan {len(lines) - 40} commit lainnya"]
        return lines
    raw = git(
        "log", "--no-merges", "--date=short", *ignore_bot,
        "--pretty=- `%h` %s _(%ad)_", "-15",
    )
    return raw.splitlines() or ["- (riwayat tidak tersedia)"]


def read_source(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                data[k.strip()] = v.strip()
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", default="dist")
    parser.add_argument("--meta", default="dist/meta.json")
    parser.add_argument("--out", default="release-notes.md")
    parser.add_argument("--changelog", default="changelog-section.md")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--run", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--event", default="")
    parser.add_argument("--force", default="0")
    args = parser.parse_args()

    token = os.environ.get("GH_TOKEN", "")
    if not token:
        print("::error::GH_TOKEN tidak tersedia")
        sys.exit(1)

    dist = Path(args.dist)
    zips = sorted(dist.glob("*.zip"))
    if not zips:
        print("::error::zip tidak ditemukan di artifact")
        sys.exit(1)
    zip_path = zips[0]
    checksums_path = dist / "checksums.txt"

    checksums = checksums_path.read_text().strip() if checksums_path.exists() else ""
    match = re.search(r"^([0-9a-f]{64})", checksums, re.M)
    new_sha = match.group(1) if match else ""
    if not new_sha:
        print("::error::sha256 zip tidak terbaca dari checksums.txt")
        sys.exit(1)

    meta = json.loads(Path(args.meta).read_text())
    old_state_path = Path(".upstream-state.json")
    old_state = json.loads(old_state_path.read_text()) if old_state_path.exists() else {}

    # ---------- 1. deteksi duplikat ----------
    releases = api(f"{API}/repos/{args.repo}/releases?per_page=10", token) or []
    releases = [r for r in releases if not r.get("draft")]
    latest = releases[0] if releases else None
    duplicate = False
    if latest:
        asset = next((a for a in latest.get("assets", []) if a.get("name") == "checksums.txt"), None)
        if asset:
            blob = download_asset(asset, token)
            if blob:
                prev_match = re.search(rb"^([0-9a-f]{64})", blob, re.M)
                if prev_match and prev_match.group(1).decode() == new_sha:
                    duplicate = True
    if duplicate and args.force == "1":
        print("zip identik dengan rilis terakhir, tetapi --force 1 → rilis tetap dibuat")
        duplicate = False

    summary_lines = []
    if duplicate:
        summary_lines.append(
            f"Rilis dilewati: zip identik dengan `{latest.get('tag_name')}` "
            f"(sha256 `{new_sha[:16]}…`). Tidak ada perubahan biner."
        )

    # ---------- 2. susun changelog ----------
    prev_tag = git("describe", "--tags", "--abbrev=0", "--match", "avenia-gs101-r*")
    table, details = upstream_changes(old_state, meta, token)
    ds = read_source(Path("configs/droidspaces.source"))

    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    title = f"Avenia gs101 r{args.run}"

    sections: list[str] = []
    sections.append(f"**Avenia Kernel by aryarifki** — gs101 (Pixel 6 / 6 Pro / 6a)")
    sections.append("")
    sections.append(
        f"Build `run #{args.run}` · commit `{args.sha[:12]}` · event `{args.event}` · {date}"
    )
    sections.append("")
    sections.append("### Ringkasan upstream")
    sections.append("")
    sections.extend(table)
    sections.append("")
    if not old_state:
        sections.append("Rilis **baseline** — belum ada state upstream sebelumnya untuk dibandingkan.")
    elif details:
        sections.append("### Perubahan upstream (detail commit)")
        sections.append("")
        sections.extend(details)
    else:
        sections.append("### Perubahan upstream (detail commit)")
        sections.append("")
        sections.append("Tidak ada perubahan SHA upstream dibanding rilis sebelumnya.")
        sections.append("")

    sections.append("### Perubahan repo ini")
    sections.append("")
    sections.extend(repo_changes(prev_tag))
    sections.append("")

    sections.append("### Identitas kernel")
    sections.append("")
    sections.append("| Item | Nilai |")
    sections.append("|---|---|")
    sections.append(f"| `uname -r` | `…{meta.get('localversion', '')}` |")
    sections.append(f"| Banner dmesg | `Avenia Kernel by aryarifki` (patch 9005) |")
    sections.append(f"| SUSFS | `{meta.get('susfs', 'unknown')}` |")
    sections.append(f"| KernelSU | `{meta.get('ksu_version', 'unknown')}` |")
    sections.append(f"| Clang | `{meta.get('clang', 'unknown')}` |")
    sections.append(
        f"| DroidSpaces | upstream `{short(ds.get('UPSTREAM_SHA', ''))}` · "
        f"{ds.get('REQUIREMENTS_COUNT', '?')} requirement |"
    )
    sections.append("")

    patches = meta.get("patches", [])
    if patches:
        sections.append("### Patch stack yang dibangun")
        sections.append("")
        sections.append("| Patch | sha256 |")
        sections.append("|---|---|")
        for patch in patches:
            sections.append(f"| `{patch.get('file')}` | `{patch.get('sha256', '')[:16]}…` |")
        sections.append("")

    sections.append("### Verifikasi sebelum flash")
    sections.append("")
    sections.append("```bash")
    sections.append(f"sha256sum {zip_path.name}   # harus sama dengan blok Checksum di bawah")
    sections.append("unzip -p Avenia-gs101-ksu-release.zip anykernel.sh | grep kernel.string")
    sections.append("#   → kernel.string=Avenia Kernel by aryarifki")
    sections.append("```")
    sections.append("")
    sections.append("Device-check AK3: `oriole` / `raven` / `bluejay` — salah device akan ditolak.")
    sections.append("")
    sections.append("### Checksum")
    sections.append("")
    sections.append("```")
    sections.append(checksums)
    sections.append("```")
    sections.append("")
    sections.append(
        "Kredit: Reinazhard (kernel staging, fork KernelSU, scripts/AnyKernel3) · "
        "simonpunk (SUSFS) · tiann (KernelSU) · osm0sis dkk (AnyKernel3) · "
        "ravindu644 (DroidSpaces) · AOSP (clang) — detail: DOKUMENTASI.md"
    )
    sections.append("")

    body = "\n".join(sections)
    Path(args.out).write_text(body)

    changelog = [
        f"## r{args.run} — {date}",
        "",
        f"Build `{args.sha[:12]}` · event `{args.event}` · `{zip_path.name}`",
        "",
        "| Komponen | Sebelumnya | Sekarang |",
        "|---|---|---|",
    ]
    for row in table[2:]:
        changelog.append(row.replace("| Status |", "").rsplit("|", 2)[0] + "|")
    changelog.append("")
    changelog.extend(repo_changes(prev_tag))
    changelog.append("")
    changelog.append("```")
    changelog.append(checksums)
    changelog.append("```")
    changelog.append("")
    Path(args.changelog).write_text("\n".join(changelog))

    print(f"changelog: {args.out} ({len(body)} byte) · duplikat={duplicate}")
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as fh:
            fh.write(f"duplicate={'true' if duplicate else 'false'}\n")
            fh.write(f"zip_sha={new_sha}\n")
            fh.write(f"zip_name={zip_path.name}\n")


if __name__ == "__main__":
    main()
