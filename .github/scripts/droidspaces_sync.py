#!/usr/bin/env python3
"""Sinkronisasi requirement kernel DroidSpaces dari upstream.

Sumber kebenaran: ravindu644/droidspaces-oss
  - Documentation/Kernel-Configuration.md  -> blok "Step 2: Edit the GKI defconfig"
  - Documentation/resources/kernel-patches/GKI/below-kernel-6.12/001...patch

Yang dihasilkan:
  configs/droidspaces.requirements  (daftar CONFIG_*=y, dipakai build + quality gate)
  configs/droidspaces.source        (pin SHA upstream, hash dokumen & patch kABI)

Patch kABI TIDAK pernah ditimpa otomatis: patches/9001 milik repo ini sudah
diadaptasi ke slot padding task_struct tree guacamole_sickness (slot 1-3 terpakai,
dipakai slot 6-8). Jika hash patch upstream berubah, skrip hanya menandai
PATCH_CHANGED=1 agar workflow membuka issue untuk review manusia.
"""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UPSTREAM_DIR = ROOT / "upstream-ds"
DOC = UPSTREAM_DIR / "Documentation" / "Kernel-Configuration.md"
KABI = (
    UPSTREAM_DIR
    / "Documentation"
    / "resources"
    / "kernel-patches"
    / "GKI"
    / "below-kernel-6.12"
    / "001.GKI-below-6.12-fix_sysvipc_kabi_6_7_8.patch"
)
REQ_FILE = ROOT / "configs" / "droidspaces.requirements"
SRC_FILE = ROOT / "configs" / "droidspaces.source"

# Dua simbol ini sengaja dilarang: merusak kABI modul vendor prebuilt (bootloop).
FORBIDDEN = {"CONFIG_CFS_BANDWIDTH", "CONFIG_CGROUP_PIDS"}

# Nama simbol yang berubah di kernel modern (>= 4.18). Dokumen upstream masih
# menuliskan nama lama karena mendukung kernel 3.10+, dan blok GKI-nya ikut
# terbawa. Tanpa pemetaan ini, `make defconfig` membuang simbol tak dikenal
# secara diam-diam → quality gate gagal (build #12: NETFILTER_XT_TARGET_REJECT).
RENAMED = {
    # xt_REJECT dipecah per-family: ipt_REJECT (IPv4) + ip6t_REJECT (IPv6).
    "CONFIG_NETFILTER_XT_TARGET_REJECT": [
        "CONFIG_IP_NF_TARGET_REJECT",
        "CONFIG_IP6_NF_TARGET_REJECT",
    ],
}


def die(msg: str) -> None:
    print(f"::error::{msg}")
    sys.exit(1)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(UPSTREAM_DIR), *args], text=True
    ).strip()


def read_source() -> dict[str, str]:
    data: dict[str, str] = {}
    if SRC_FILE.exists():
        for line in SRC_FILE.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                data[k.strip()] = v.strip()
    return data


def extract_gki_block(text: str) -> str:
    """Ambil blok Step 2 HANYA di dalam section 'GKI kernels'.

    Dokumen upstream punya beberapa '### Step 2' (non-GKI, GKI, dst). Anchor ke
    heading '## GKI kernels' dulu supaya tidak mengambil daftar non-GKI.
    """
    gki = re.search(r"^## GKI kernels.*$", text, re.M)
    if not gki:
        die("section '## GKI kernels' tidak ditemukan di dokumen upstream")
    section = text[gki.end():]
    nxt = re.search(r"^## ", section, re.M)
    if nxt:
        section = section[: nxt.start()]
    start = re.search(r"^### Step 2:[^\n]*\n", section, re.M)
    if not start:
        die("blok 'Step 2: Edit the GKI defconfig' tidak ditemukan di section GKI")
    rest = section[start.end():]
    end = re.search(r"^### Step 3", rest, re.M)
    return rest[: end.start()] if end else rest


def parse_requirements(block: str) -> list[str]:
    symbols: list[str] = []
    for raw in block.splitlines():
        line = raw.strip()
        if line.startswith("#") or line.startswith(">"):
            continue
        m = re.match(r"^(CONFIG_[A-Z0-9_]+)=y$", line)
        if not m:
            continue
        sym = m.group(1)
        if sym in FORBIDDEN:
            continue
        for resolved in RENAMED.get(sym, [sym]):
            if resolved in FORBIDDEN:
                continue
            if resolved not in symbols:
                symbols.append(resolved)
    return symbols


def render_requirements(symbols: list[str], upstream_sha: str, upstream_date: str) -> str:
    lines = [
        "# DroidSpaces — requirement defconfig untuk Avenia (GKI 6.1 / android14-6.1)",
        f"# Sumber: ravindu644/droidspaces-oss @ {upstream_sha[:12]} ({upstream_date})",
        "# Dokumen: Documentation/Kernel-Configuration.md → 'GKI kernels' → Step 2",
        "#",
        "# DIGENERATE OTOMATIS oleh .github/workflows/sync-droidspaces.yml.",
        "# Jangan edit manual — perubahan akan tertimpa pada sinkronisasi berikutnya.",
        "#",
        "# CATATAN ABI: CONFIG_CFS_BANDWIDTH dan CONFIG_CGROUP_PIDS sengaja TIDAK ada",
        "# di sini. Keduanya mengubah ukuran struktur scheduler/cgroup dan menggeser",
        "# CRC ribuan simbol vendor → modul stok Pixel 6 menolak load (bootloop).",
        "#",
        "# CATATAN NAMA: dokumen upstream memakai nama lama (mendukung 3.10+).",
        "# CONFIG_NETFILTER_XT_TARGET_REJECT tidak ada di 6.1 → dipetakan otomatis ke",
        "# CONFIG_IP_NF_TARGET_REJECT + CONFIG_IP6_NF_TARGET_REJECT (lihat RENAMED).",
        "",
    ]
    lines.extend(f"{sym}=y" for sym in symbols)
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    if not DOC.exists():
        die(f"dokumen upstream tidak ditemukan: {DOC}")
    if not KABI.exists():
        die(f"patch kABI upstream tidak ditemukan: {KABI}")

    upstream_sha = git("rev-parse", "HEAD")
    upstream_date = git("log", "-1", "--format=%cs")

    symbols = parse_requirements(extract_gki_block(DOC.read_text()))
    if len(symbols) < 5:
        die(f"hanya {len(symbols)} simbol terbaca — format dokumen upstream berubah?")
    if FORBIDDEN & set(symbols):
        die("dokumen upstream memuat simbol terlarang (CFS_BANDWIDTH/CGROUP_PIDS)")

    new_req = render_requirements(symbols, upstream_sha, upstream_date)
    old_req = REQ_FILE.read_text() if REQ_FILE.exists() else ""
    old_src = read_source()

    doc_hash = sha256(DOC)
    kabi_hash = sha256(KABI)

    req_changed = new_req != old_req
    patch_changed = bool(old_src.get("KABI_PATCH_SHA256")) and (
        old_src["KABI_PATCH_SHA256"] != kabi_hash
    )

    REQ_FILE.parent.mkdir(parents=True, exist_ok=True)
    REQ_FILE.write_text(new_req)

    src = "\n".join(
        [
            "# Pin sumber DroidSpaces — digenerate otomatis, jangan edit manual.",
            "UPSTREAM_REPO=ravindu644/droidspaces-oss",
            f"UPSTREAM_SHA={upstream_sha}",
            f"UPSTREAM_DATE={upstream_date}",
            f"DOC_SHA256={doc_hash}",
            f"KABI_PATCH={KABI.relative_to(UPSTREAM_DIR)}",
            f"KABI_PATCH_SHA256={kabi_hash}",
            f"REQUIREMENTS_COUNT={len(symbols)}",
            "REQUIREMENTS_FILE=configs/droidspaces.requirements",
            f"SYNCED_AT={datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
            "",
        ]
    )
    SRC_FILE.write_text(src)

    print(f"upstream      : {upstream_sha[:12]} ({upstream_date})")
    print(f"dokumen sha   : {doc_hash[:16]}…")
    print(f"patch kABI sha: {kabi_hash[:16]}…")
    print(f"requirement   : {len(symbols)} simbol")
    print(f"requirements berubah: {req_changed}")
    print(f"patch kABI berubah  : {patch_changed}")

    if old_src.get("UPSTREAM_SHA") == upstream_sha and not req_changed:
        print("status: sudah sinkron dengan upstream HEAD")

    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as fh:
            fh.write(f"requirements_changed={'true' if req_changed else 'false'}\n")
            fh.write(f"patch_changed={'true' if patch_changed else 'false'}\n")
            fh.write(f"upstream_sha={upstream_sha}\n")
            fh.write(f"requirements_count={len(symbols)}\n")


if __name__ == "__main__":
    main()
