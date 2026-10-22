# 🌿 DOKUMENTASI LENGKAP — Avenia Kernel (gs101 / Pixel 6)

> **AVENIA KERNEL • by aryarifki**
> Kernel android14-6.1 device-matched untuk Pixel 6 / 6 Pro (raviole; 6a/bluejay juga dilindungi device-check AK3),
> driver root **KernelSU fork** + integrasi **SUSFS**, dibangun otomatis oleh CI dengan sumber upstream yang selalu segar.

---

## 0. KREDIT & ATRIBUSI — upfront, wajib dibaca

Avenia adalah *rebrand* di atas kerja komunitas. **Tidak ada satu komponen upstream yang semantiknya diubah.**
Kredit tangan-pertama (paling berpengaruh teratas):

| Pihak | Karya | Peran di Avenia |
|---|---|---|
| **Reinazhard** | `guacamole_sickness` (branch `staging`) | Sumber tree kernel utama (android14-6.1, tuning Pixel 6, slot kABI) |
| **Reinazhard** | `KernelSU` (branch `fork`) | Driver root bawaan Avenia — sudah mengandung integrasi KernelSU × SUSFS matang |
| **Reinazhard** | `scripts/raviole/build.sh` + `AnyKernel3` | Logika build device-matched + pack zip flashable |
| **simonpunk** | `susfs4ksu` (GitLab) | SUSFS — lapisan root-hiding (keluarga ABI v2.3) |
| **tiann (Weishu)** | `KernelSU` | Proyek induk driver root & manager resmi `me.weishu.kernelsu` |
| **osm0sis dkk** | AnyKernel3 upstream | Kerangka flashable zip (AK3) universal yang ditopang seluruh ekosistem |
| **Tim DroidSpaces** | aplikasi & spesifikasi config | Tujuan kompatibilitas patch 9002/9003 (namespace/IPC/exempt daemon susfs) |
| **AOSP / Google** | prebuilt clang r614150 | Toolchain build (`CLANG_SOURCE=aosp`) |
| **aryarifki** | repo `Avenia-gs101` ini | Resep CI, patch 9004–9005 (identitas Avenia), dokumentasi & rilis |

Lisensi keseluruhan: **GPL-2.0** (pewarisan upstream). Kredit ini juga tercantum di README-CI
dan di body setiap rilis otomatis.

### Apa persisnya yang Avenia ubah dari upstream (transparansi mutlak)

1. `9004` → `CONFIG_LOCALVERSION="-Avenia"` (1 baris defconfig — nama kernel).
2. `9005` → banner dmesg `Avenia Kernel by aryarifki || welcome to KernelSU …` (1 baris string `pr_info`).
3. `kernel.string` di anykernel.sh → `Avenia Kernel by aryarifki` (sed di CI, bukan patch source).
4. Nama zip/artifact/workflow → *Avenia*.

**Yang TIDAK pernah disentuh:** `KSU_VERSION` (gating fitur manager), `KSU_PACKAGE_NAME`
(deteksi manager APK), kode driver root, struct selinux/susfs, tuning defconfig — semuanya
milik upstream utuh.

---

## 1. Identitas kernel — di mana apa muncul

| Permukaan | Nilai di Avenia |
|---|---|
| `uname -r` / `/proc/version` | memuat `-Avenia` |
| `dmesg` saat boot | `Avenia Kernel by aryarifki \|\| welcome to KernelSU version 32680, package name me.weishu.kernelsu` |
| Layar flash (ui_print AK3) | `kernel.string=Avenia Kernel by aryarifki` |
| Nama zip | `Avenia-gs101-ksu-release.zip` |
| Nama artifact Actions | `avenia-gs101-ksu-release-droidspaces` |
| Nama release otomatis | `Avenia gs101 r<N>` (tag `avenia-gs101-r<N>`) |
| Nama repo / workflow | `aryarifki/Avenia-gs101` / `build-avenia-gs101-droidspaces` |

## 2. Arsitektur build (pola "resep", bukan fork)

```
aryarifki/Avenia-gs101  (±60 KB — resep)
 ├── .github/workflows/build-kernel.yml   ← otak CI
 ├── patches/9001…9005                    ← lapisan kompos
 └── README-CI.md + DOKUMENTASI.md        ← dokumentasi

          └── saat CI jalan, runner meng-clone segar:
                ├─ https://github.com/Reinazhard/guacamole_sickness  @staging  → tree kernel utama
                ├─ https://github.com/Reinazhard/scripts                       → build.sh raviole
                ├─ https://github.com/Reinazhard/KernelSU            @fork     → kernel/KernelSU (driver root)
                └─ https://github.com/Reinazhard/AnyKernel3                    → kernel/AnyKernel3 (pembungkus zip)
```

Keuntungan pola ini: repo tetap kecil, HEAD upstream diikuti (rebuild mingguan otomatis),
tanpa beban merge pohon kernel ~2 GB. Fork penuh hanya masuk akal jika Anda berubah menjadi
developer kernel aktif atau butuh HEAD terkunci (reproducible).

## 3. Stack patch 9001–9005

| # | Target | Makna |
|---|---|---|
| `9001` | kABI `sysvipc` slot 6–8 (GKI <6.12) | Menjaga layout struct IPC sesuai ekspektasi modul vendor (pengganti `9001b` slot 1–3 sengaja tidak dipakai — pasti gagal di tree ini) |
| `9002` | `raviole_defconfig` | Namespace/IPC + fitur gaya DroidSpaces (`UTS_NS … TMPFS_POSIX_ACL`) — quality gate menegakkan 13 config `=y` |
| `9003` | Exempt daemon `droidspacesd` dari SUSFS | Daemon DroidSpaces melihat mount tree asli; root-hiding app lain tetap normal |
| `9004` | `CONFIG_LOCALVERSION` | `-86hm` → `-Avenia` (identitas kernel) |
| `9005` | `KernelSU/kernel/core/init.c` | Banner dmesg Avenia (string `pr_info`; `KSU_VERSION` & `KSU_PACKAGE_NAME` dijaga) |

## 4. Pipeline CI — step-by-step

1. **Bebaskan disk** — buang SDK/.NET/CodeQL preinstalled (~+25 GB bebas).
2. **Dependencies host** — `bc bison build-essential cpio dwarves flex kmod libssl-dev libncurses-dev rsync wget zip`.
3. **Clone segar** — tree staging + build.sh + fork + AK3 (lihat §2).
4. **Terapkan patch DroidSpaces** — urut leksikografis `9001→9005` (`patch -p1 --forward`).
5. **Pre-clone AK3 + branding Avenia** — build.sh menghormati AK3 yang sudah ada; sed `kernel.string`.
6. **Build** — `CLANG_SOURCE=aosp IS_RELEASE=1 KSU=1 ZIPNAME=Avenia bash ../scripts/raviole/build.sh`
   → profil release (LTO + CFI/SCS aktif) → zip jatuh di `kernel/AnyKernel3/Avenia-gs101-ksu-release.zip`.
7. **Quality gate** — 13 config DroidSpaces wajib `=y`; `CFS_BANDWIDTH`/`CGROUP_PIDS` wajib tetap off.
8. **Upload artifact** — zip (retensi 14 hari) + `build-log-failed` (3 hari, hanya bila merah).
9. **Rilis otomatis** — per build sukses: tag `avenia-gs101-r<N>` di halaman **Releases**
   berisi zip + `checksums.txt` + catatan (kredit upstream, metadata build).
10. **Upload log gagal** — hanya saat build merah, untuk diagnostik.

Trigger: push pada `patches/**` • manual *Run workflow* • cron mingguan `0 3 * * 1` (Senin 03:00 UTC).

## 5. Verifikasi binary-first SEBELUM flash (disiplin wajib)

```bash
# (A) checksum — bandingkan dengan checksums.txt di halaman rilis
sha256sum Avenia-gs101-ksu-release.zip

# (B) isi zip
unzip -l Avenia-gs101-ksu-release.zip
unzip -p Avenia-gs101-ksu-release.zip anykernel.sh | grep kernel.string
#   → harus: kernel.string=Avenia Kernel by aryarifki

# (C) kallsyms & banner di dalam Image
python3 - <<'PY'
import zipfile, re, gzip
z = zipfile.ZipFile('Avenia-gs101-ksu-release.zip')
img = z.read('Image')
try:
    img = gzip.decompress(img)          # bila disimpan sebagai Image.gz
except OSError:
    pass
print('ksu_handle_* :', len(set(re.findall(rb'ksu_handle_[a-z_]+', img))))
print('susfs_*      :', len(set(re.findall(rb'\bsusfs_[a-z_]+', img))))
print('banner Avenia:', b'Avenia Kernel by aryarifki' in img)
PY

# (D) pasca-flash (di HP, shell root):
dmesg | grep Avenia     # banner sekali saat init driver
cat /proc/version       # memuat -Avenia
```

## 6. Prosedur flash

1. Unduh zip dari halaman **Releases** (tag `avenia-gs101-rN`) — verifikasi sha256 (§5.A).
2. Pindahkan zip ke `/sdcard/Download` (via adb / atau unduh langsung di HP).
3. (Opsional) Jalankan **Check Requirements** di app DroidSpaces dulu — bila botol FAIL, jangan flash.
4. Reboot ke Recovery (TWRP / Lineage Recovery → Apply update → Apply from SDcard).
5. Pilih zip — AK3 mengecek device (`oriole/raven/bluejay`); device mism takkan dipaksa flash ✓.
6. Boot → cek banner (§5.D) → buka app **manager resmi KernelSU** (`me.weishu.kernelsu`) → root granted.
7. (Opsional) Toggle susfs via app keluarga ReSukiSU/SukiSU-Ultra — reboot-magic `0xFAFAFAFA` passthrough tetap jalan.

## 7. Recovery & fallback

| Skenario | Penanganan |
|---|---|
| Avenia bermasalah pasca-flash | Flash balik zip **86hm** dari release `droidspaces-build-1` (fallback terbukti: run #2 & #4 hijau) |
| Bootloop-total | `fastboot flash boot boot-stock-gs101.img` (boot.img stok gs101) |
| Artifact hilang (retensi 14 hari) | Ambil dari halaman Releases — asset release permanen |

## 8. Troubleshooting & catatan belajar

- **Build merah** → unduh artifact `build-log-failed` → identifikasi step yang gagal:
  patch tidak apply (drift upstream?) • Kconfig parse (struktur blok menu?) • C compile (simbol?).
  Perbaiki patch → push → CI rebuild otomatis.
- **Post-mortem historis** (percobaan Avenia pertama — fork backslashxx): semua patch apply bersih
  TAPI `make raviole_defconfig` gagal — akar masalah: skrip generator memilih `menu "KernelSU"`
  yang pertama (baris 1, menu induk) alih-alih `menu "KernelSU - SUSFS"` (baris 37) → blok yang
  disuntikkan tak menutup menu induk → Kconfig unbalanced. Pelajaran: validasi `git apply --check`
  menangkap *aplikasi-bersih* saja, titik; **semantik Kconfig perlu gate tersendiri** (tidak relevan
  untuk build produk ini karena fork Reinazhard sudah builtin susfs — tidak ada injeksi Kconfig).
- **App DroidSpaces "Check Requirements" FAIL** → kirim `build.log` + `out/.config` untuk diagnosa.

## 9. Roadmap opsional

- Bernalah bertahap: branding semakin dalam (string internal fork) = patch kecil saat berminat.
- `prerelease: true` bisa ditambahkan di step rilis untuk build eksperimen (debug flag).
- Broaden multi-device ala GKID (matrix 5 KMI) akan kehilangan ketegasan device-matched —
  tidak direkomendasikan untuk pemegang perangkat tunggal.

## 10. Glosarium

- **GKI** — Generic Kernel Image; inti kernel standar Android, bagian device-spesifik hidup di modul vendor.
- **KMI** — Kernel Module Interface; kontrak ABI antar modul vendor (contoh band: `android14-6.1`).
- **SUSFS** — lapisan kernel untuk root-hiding (hide mounts/paths untuk procs non-su) oleh simonpunk.
- **AK3 / AnyKernel3** — framework zip flashable universal (repack boot.img di recovery).
- **Artifact vs Release** — artifact = penyimpanan sementara hasil build (14 hari); Release = halaman publik permanen + asset.

---

*Repo: `aryarifki/Avenia-gs101` — teks ini disusun 2026-10-22, memovalidasi terhadap build r6 (green).*
