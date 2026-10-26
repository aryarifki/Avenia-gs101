#!/usr/bin/env python3
"""Smoke test artefak zip Avenia SEBELUM diunggah / dirilis.

Tujuan: build bisa hijau tapi zip cacat (Image hilang, dtbo kosong, branding
tidak masuk, checksum tidak cocok). Skrip ini memeriksa isi zip, bukan sekadar
keberadaan file, dan sengaja **gagal keras** — lebih baik build merah di sini
daripada pengguna mem-flash zip rusak.

Yang diperiksa:
  1. tepat satu *.zip di --dist, arsip valid (CRC semua entri diuji)
  2. anykernel.sh: kernel.string Avenia, device oriole/raven/bluejay,
     do.devicecheck=1, do.modules=0, flash_generic dtbo
  3. image kernel ada (Image / Image.gz / Image.lz4), bisa dibuka, dan
     benar-benar kernel yang dimaksud: banner "Linux version ..." + "-Avenia"
  4. dtb (magic FDT 0xd00dfeed) + dtbo.img (magic Android 0xd7b7ab1e)
  5. checksums.txt cocok dengan sha256 zip

Hanya stdlib: tidak butuh unzip/lz4 di runner.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import re
import struct
import sys
import zipfile
from pathlib import Path

EXPECTED_KERNEL_STRING = "Avenia Kernel by aryarifki"
EXPECTED_DEVICES = ("oriole", "raven", "bluejay")
MIN_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_BYTES = 256 * 1024 * 1024

LZ4_LEGACY_MAGIC = b"\x02\x21\x4c\x18"
LZ4_FRAME_MAGIC = b"\x04\x22\x4d\x18"
FDT_MAGIC = b"\xd0\x0d\xfe\xed"
DTBO_MAGIC = b"\xd7\xb7\xab\x1e"


class Report:
    def __init__(self) -> None:
        self.rows: list[tuple[bool | None, str, str]] = []
        self.failed = 0

    def check(self, ok: bool, name: str, detail: str = "") -> bool:
        self.rows.append((bool(ok), name, detail))
        if not ok:
            self.failed += 1
        return bool(ok)

    def warn(self, name: str, detail: str = "") -> None:
        self.rows.append((None, name, detail))

    def render(self) -> None:
        width = max(len(r[1]) for r in self.rows) + 2
        for ok, name, detail in self.rows:
            mark = "OK  " if ok else ("WARN" if ok is None else "FAIL")
            print(f"  [{mark}] {name:<{width}} {detail}")
        print()
        if self.failed:
            print(f"HASIL: GAGAL — {self.failed} pemeriksaan tidak lolos")
        else:
            print(f"HASIL: LULUS — {len(self.rows)} pemeriksaan")


def lz4_legacy_decompress(data: bytes, limit: int = MAX_IMAGE_BYTES) -> bytes:
    """Dekode frame LZ4 legacy (magic 0x184C2102) tanpa dependensi eksternal.

    Format: magic, lalu blok berulang [4B ukuran LE][data]; bit tertinggi =
    blok tidak dikompresi; ukuran 0 = akhir. Setiap blok = LZ4 block format.
    """
    if not data.startswith(LZ4_LEGACY_MAGIC):
        raise ValueError("bukan frame LZ4 legacy")
    out = bytearray()
    pos = 4
    total = len(data)
    while pos + 4 <= total:
        size = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        if size == 0:
            break
        raw = bool(size & 0x80000000)
        size &= 0x7FFFFFFF
        if size > total - pos:
            raise ValueError("blok terpotong")
        chunk = data[pos:pos + size]
        pos += size
        if raw:
            out += chunk
            continue
        # LZ4 block decode
        i, n = 0, len(chunk)
        while i < n:
            token = chunk[i]
            i += 1
            literals = token >> 4
            if literals == 15:
                while i < n:
                    byte = chunk[i]
                    i += 1
                    literals += byte
                    if byte != 255:
                        break
            out += chunk[i:i + literals]
            i += literals
            if i >= n:
                break
            offset = chunk[i] | (chunk[i + 1] << 8)
            i += 2
            length = (token & 0x0F) + 4
            if (token & 0x0F) == 15:
                while i < n:
                    byte = chunk[i]
                    i += 1
                    length += byte
                    if byte != 255:
                        break
            start = len(out) - offset
            if start < 0:
                raise ValueError("offset LZ4 di luar jendela")
            for k in range(length):
                out.append(out[start + k])
        if len(out) > limit:
            raise ValueError("hasil dekompresi melebihi batas")
    return bytes(out)


def extract_kernel_image(zf: zipfile.ZipFile, report: Report) -> bytes | None:
    candidates = [n for n in ("Image", "Image.gz", "Image.lz4") if n in zf.namelist()]
    if not report.check(len(candidates) == 1, "image kernel (tepat satu)",
                        ", ".join(candidates) or "tidak ada Image/Image.gz/Image.lz4"):
        return None
    name = candidates[0]
    blob = zf.read(name)
    report.check(len(blob) > 1_000_000, f"ukuran {name}", f"{len(blob) / 1e6:.1f} MB")
    try:
        if name.endswith(".lz4"):
            if blob.startswith(LZ4_LEGACY_MAGIC):
                raw = lz4_legacy_decompress(blob)
            elif blob.startswith(LZ4_FRAME_MAGIC):
                raise ValueError("frame LZ4 modern — belum didukung skrip ini")
            else:
                raise ValueError(f"magic tidak dikenal: {blob[:4].hex()}")
        elif name.endswith(".gz"):
            raw = gzip.decompress(blob)
        else:
            raw = blob
    except Exception as exc:  # noqa: BLE001
        report.check(False, f"dekompresi {name}", str(exc))
        return None
    report.check(MIN_IMAGE_BYTES < len(raw) <= MAX_IMAGE_BYTES,
                 f"dekompresi {name}", f"{len(raw) / 1e6:.1f} MB")
    return raw


def check_anykernel(text: str, report: Report) -> None:
    lines = [ln.strip() for ln in text.splitlines()]
    strings = [ln for ln in lines if ln.startswith("kernel.string=")]
    report.check(
        strings == [f"kernel.string={EXPECTED_KERNEL_STRING}"],
        "kernel.string",
        strings[0] if strings else "tidak ditemukan",
    )
    devices = {ln.split("=", 1)[1] for ln in lines
               if ln.startswith("device.name") and "=" in ln}
    missing = [d for d in EXPECTED_DEVICES if d not in devices]
    report.check(not missing, "device.name oriole/raven/bluejay",
                 f"hilang: {', '.join(missing)}" if missing else "lengkap")
    report.check("do.devicecheck=1" in lines, "do.devicecheck=1")
    report.check("do.modules=0" in lines, "do.modules=0",
                 "modul vendor tidak boleh ditimpa")
    report.check("flash_generic dtbo" in text, "flash_generic dtbo",
                 "dtbo Pixel wajib ter-flash")
    versions = [ln for ln in lines if ln.startswith("supported.versions=")]
    if versions:
        report.warn("supported.versions", versions[0].split("=", 1)[1])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", default="out", help="folder berisi zip + checksums.txt")
    parser.add_argument("--expect-version", default=r"6\.1\.",
                        help="regex versi kernel yang diharapkan di banner")
    args = parser.parse_args()

    dist = Path(args.dist)
    report = Report()

    zips = sorted(dist.glob("*.zip")) if dist.is_dir() else []
    if not report.check(len(zips) == 1, "tepat satu zip di dist",
                        ", ".join(p.name for p in zips) or f"{dist} kosong"):
        report.render()
        return 1
    zip_path = zips[0]

    report.check(zip_path.stat().st_size > 5_000_000, "ukuran zip",
                 f"{zip_path.stat().st_size / 1e6:.1f} MB")

    with zipfile.ZipFile(zip_path) as zf:
        bad = zf.testzip()
        report.check(bad is None, "integritas CRC zip", bad or "semua entri utuh")

        names = zf.namelist()
        report.check("anykernel.sh" in names, "anykernel.sh ada")
        if "anykernel.sh" in names:
            check_anykernel(zf.read("anykernel.sh").decode("utf-8", "ignore"), report)

        image = extract_kernel_image(zf, report)
        if image is not None:
            banner = re.search(rb"Linux version (\d+\.\d+\.\d+[^\s\x00]*)", image)
            report.check(banner is not None, "banner 'Linux version' di Image",
                         banner.group(1).decode() if banner else "tidak ditemukan")
            report.check(b"-Avenia" in image, "identitas '-Avenia' di Image",
                         f"{image.count(b'-Avenia')} kemunculan")
            report.check(EXPECTED_KERNEL_STRING.encode() in image,
                         "banner Avenia di Image",
                         f"{image.count(EXPECTED_KERNEL_STRING.encode())} kemunculan")
            if banner:
                report.check(bool(re.search(args.expect_version, banner.group(1).decode())),
                             "versi kernel sesuai", banner.group(1).decode())

        if "dtb" in names:
            report.check(zf.read("dtb")[:4] == FDT_MAGIC, "magic dtb (FDT)",
                         zf.read("dtb")[:4].hex())
        else:
            report.check(False, "dtb ada")

        if "dtbo.img" in names:
            report.check(zf.read("dtbo.img")[:4] == DTBO_MAGIC, "magic dtbo.img",
                         zf.read("dtbo.img")[:4].hex())
        else:
            report.check(False, "dtbo.img ada")

        stray_modules = [n for n in names if n.startswith("modules/")]
        if stray_modules:
            report.warn("modul di dalam zip", f"{len(stray_modules)} entri (do.modules=0)")

        checksums = dist / "checksums.txt"
        if report.check(checksums.is_file(), "checksums.txt ada"):
            digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
            match = re.search(
                rf"^([0-9a-f]{{64}})\s+\*?{re.escape(zip_path.name)}$",
                checksums.read_text(), re.M,
            )
            report.check(match is not None, "checksums.txt memuat entri zip")
            report.check(bool(match) and match.group(1) == digest,
                         "sha256 zip = checksums.txt",
                         digest[:16] + "…")

    report.render()
    return 1 if report.failed else 0


if __name__ == "__main__":
    sys.exit(main())
