# Build Otomatis Avenia Kernel (gs101) + DroidSpaces via GitHub Actions

> Jawaban singkat: **TIDAK harus dari terminal ini.** Cara paling praktis = GitHub
> Actions (gratis, tidak makan disk lokal, tidak perlu toolchain lokal). Build
> dari terminal (proot Android) tetap *mungkin*, tapi butuh ±40 GB disk + beberapa
> jam + unduhan toolchain besar — tidak disarankan.

**Avenia Kernel by aryarifki** — rebrand penuh dari komponen upstream yang tetap
dikreditkan: kernel staging Reinazhard (`guacamole_sickness`/`staging`), driver
root KernelSU fork Reinazhard (branch `fork`, integrasi SUSFS builtin), build
scripts + AnyKernel3 milik Reinazhard, clang prebuilt AOSP. Identitas hasil build:
`uname -r` memuat `-Avenia`, `kernel.string=Avenia Kernel by aryarifki`, nama zip
`Avenia-gs101-ksu-release.zip`.

---

## 1. Isi folder `github-ci/`

```
github-ci/
├── .github/
│   ├── workflows/build-kernel.yml         ← build + quality gate + job rilis terpisah
│   ├── workflows/sync-droidspaces.yml     ← sinkron requirement DroidSpaces (harian 02:00 UTC)
│   └── scripts/
│       ├── release_notes.py               ← generator changelog + deteksi rilis duplikat
│       ├── droidspaces_sync.py            ← ekstraktor requirement GKI + hash patch kABI
│       └── smoke_test.py                  ← uji isi zip sebelum artifact diunggah
├── configs/
│   ├── droidspaces.requirements           ← 20 simbol GKI (auto-generated)
│   └── droidspaces.source                 ← pin SHA upstream + hash dokumen & patch kABI
├── patches/
│   ├── 9001-GKI-below-6.12-fix_sysvipc_kabi_6_7_8.patch   (kABI slot 6–8)
│   ├── 9002-DroidSpaces-raviole_defconfig.patch           (config namespace+IPC)
│   ├── 9003-exempt-droidspacesd-susfs.patch               (exemption domain droidspacesd)
│   ├── 9004-avenia-rebrand.patch                          (rebrand: LOCALVERSION "-Avenia")
│   ├── 9005-avenia-ksu-brand.patch                        (branding dalam: banner dmesg boot Avenia)
├── CHANGELOG.md                           ← dibuat otomatis oleh job rilis (jangan edit manual)
├── DOKUMENTASI.md                         ← panduan lengkap + matriks fitur
└── README-CI.md                           ← file ini
```

Setelah repo aktif, CI juga menulis dua file status: `CHANGELOG.md` dan `.upstream-state.json`
(keduanya di-commit oleh `github-actions[bot]` dengan `[skip ci]`).

Catatan: `9001b` (fallback slot 1–3) sengaja TIDAK disertakan — itu hanya untuk
tree GKI standar, di tree staging ini dijamin gagal apply.

## 2. Langkah setup (tanpa terminal, ±5 menit)

1. **Buat repo baru** di akun GitHub Anda, mis. `gs101-droidspaces-build`
   (repository dapat private maupun public — public lebih aman soal kuota
   Actions gratis; private untuk repo publik kernel tetap dapat 2.000 menit/bulan).
2. **Upload isi folder ini** ke repo tersebut, jaga struktur foldernya:
   - Via web: add file → *Upload files* → drag folder yang berisi
     `.github/`, `configs/`, `patches/`, `DOKUMENTASI.md`, `README-CI.md`.
     > GitHub web tidak mengizinkan drag folder `.github` (diawali titik) —
     > solusi: upload lewat *Add file → Create new file*, ketik path
     > `.github/workflows/build-kernel.yml`, lalu paste isinya. Lakukan hal yang
     > sama untuk `sync-droidspaces.yml` dan kedua skrip di `.github/scripts/`.
   - Atau via git biasa: `git init; git add .; git commit; git push`.
   - **Wajib**: folder `configs/` harus ikut ter-upload. Tanpanya job build berhenti
     di gate requirement (`configs/droidspaces.requirements tidak ada`).
3. Buka tab **Actions** → pilih *build-avenia-gs101-droidspaces* → enable jika diminta
   → klik **Run workflow** → Run.
4. Tunggu ±1,5–4 jam (LTO+CFI di runner 4-core; build pertama paling lama).
5. Unduh artifact **`avenia-gs101-ksu-release-droidspaces`** (zip: `Avenia-gs101-ksu-release.zip`)
   → flash via Recovery/TWRP.

## 3. Apa yang dilakukan workflow (otomatis, sudah sesuai hasil analisis)

| Step | Detail |
|---|---|
| Bebaskan disk | hapus SDK Android/.NET/CodeQL preinstalled runner (~+25 GB) |
| Deps host | `bc bison flex cpio dwarves(pahole) libssl-dev kmod rsync zip` |
| Clone | kernel `staging` + `scripts` (build.sh) + KernelSU `fork` → `kernel/KernelSU` (posisi ini dihormati build.sh, tidak di-clone ulang). Bisa **di-pin** per-run lewat input `kernel_ref`/`ksu_ref`/`scripts_ref`/`ak3_ref` |
| Patch | `patch -p1` untuk kelima patch, berurutan |
| Requirement DroidSpaces | `configs/droidspaces.requirements` (digenerate dari dokumen resmi DroidSpaces, 20 simbol) di-merge ke `raviole_defconfig`; simbol terlarang (`CFS_BANDWIDTH`/`CGROUP_PIDS`) ditolak keras |
| Brand + guard AK3 | sed `kernel.string=Avenia Kernel by aryarifki`, lalu assert: `device.name*=oriole/raven/bluejay`, `do.devicecheck=1`, `do.modules=0`, `flash_generic dtbo` — build gagal bila upstream AK3 mengubah salah satunya |
| Banner dmesg | patch 9005: saat init kernel, dmesg/logcat menampilkan `Avenia Kernel by aryarifki \|\| welcome to KernelSU version …` — string log saja, tidak menyentuh `KSU_VERSION`/`KSU_PACKAGE_NAME` (aman untuk deteksi manager) |
| Build | `CLANG_SOURCE=aosp` (prebuilt, jauh lebih cepat daripada klon LLVM kernel.org), `ZIPNAME=Avenia KSU=1 IS_RELEASE=1` → zip final jatuh di `kernel/AnyKernel3/*.zip` |
| Quality gate | semua simbol di `configs/droidspaces.requirements` wajib `=y` di `out/.config`, dan `CFS_BANDWIDTH`/`CGROUP_PIDS` wajib tetap off — build gagal bila dilanggar |
| Smoke test | sebelum upload: CRC seluruh entri, `kernel.string` + device AK3, banner `-Avenia` di dalam Image (LZ4 legacy didekode stdlib), magic `dtb`/`dtbo.img`, sha256 vs `checksums.txt` — gagal = build merah, zip tidak terbit |
| Artifact | zip + `checksums.txt` + `meta.json` (retensi 14 hari) + log gagal (3 hari) |
| Rilis | job terpisah (`contents: write`): changelog lengkap, cek duplikat sha256, tag `avenia-gs101-r<N>`, update `CHANGELOG.md` + `.upstream-state.json` |

## 4. Build "otomatis" level berikutnya (opsional)

- **Build tiap kali patch berubah**: sudah aktif (trigger `push` pada `patches/**` dan `configs/**`).
- **Build terjadwal mengikuti upstream**: SUDAH AKTIF — cron `0 3 * * 1`
  (Senin 03:00 UTC / ±10:00 WIB), selalu memakai HEAD upstream saat clone
  (kernel staging, KernelSU fork, AnyKernel3, toolchain AOSP). Note: edit file
  workflow sendiri sengaja tidak lagi men-trigger build otomatis.
- **Build reproducible / rollback**: SUDAH AKTIF — input `kernel_ref`, `ksu_ref`,
  `scripts_ref`, `ak3_ref` (branch/tag/SHA) saat *Run workflow*; kosong = HEAD upstream.
- **Sinkronisasi DroidSpaces otomatis**: SUDAH AKTIF — workflow `sync-droidspaces.yml`
  (harian 02:00 UTC) mengambil `ravindu644/droidspaces-oss`, mengekstrak requirement GKI
  dari `Documentation/Kernel-Configuration.md`, dan men-dispatch build bila daftarnya
  berubah. Patch kABI upstream yang berubah → Issue untuk review (patch 9001 kita
  diadaptasi ke slot padding 6–8).
- **Release otomatis + changelog**: SUDAH AKTIF — setiap build yang menghasilkan biner
  berbeda membuat tag `avenia-gs101-r<N>`, zip + `checksums.txt` + changelog lengkap
  (perubahan upstream, perubahan repo, patch stack, SUSFS/KernelSU/clang, sha256).
  Build yang zip-nya byte-identik dengan rilis terakhir **tidak** membuat rilis baru
  (override: `force_release=1`). Panduan lengkap: **DOKUMENTASI.md**.

## 5. Kalau tetap ingin build dari terminal ini (proot Android)

Mungkin, dengan syarat keras:
1. Disk bebas ≥ 40 GB (`df -h` dulu; toolchain AOSP clang ±1,2 GB + out dir 10–25 GB).
2. Paket: `build-essential bc bison flex libssl-dev cpio dwarves rsync zip python3`.
3. clone + patch persis seperti workflow, lalu dari root tree kernel:
   ```
   CLANG_SOURCE=aosp IS_RELEASE=1 KSU=1 ZIPNAME=Avenia bash ../scripts/raviole/build.sh
   ```
4. Ekspektasi: banyak lebih lambat daripada runner CI, dan proot bisa rewel soal
   memori saat LTO (butuh swap besar). Ini urusan ±6–12 jam di ponsel/typan.

## 6. Jaga-jaga

- Jika 9001 memicu bootloop (offset kABI) → ganti patch 9001 dengan paket
  fallback `3_4_5` (URL ada di bundle `droidspaces-oriole/README-BUILD-ORIOLE.md`), commit,
  push → CI rebuild otomatis.
- Jika `Check Requirements` di app DroidSpaces masih menolak → kirim log
  `build.log` + `out/.config` (artifact) untuk kami diagnosa.

## 7. Batasan yang diketahui (dan kenapa)

**Tidak ada fitur kernel upstream yang dibuang.** Diff `raviole_defconfig` stok vs Avenia = 0 baris dihapus
(hanya `LOCALVERSION` yang diganti dan `UTS_NS`/`PID_NS` dinaikkan dari `not set` → `=y`).
Yang tidak tersedia hanyalah tiga **limit**, dan itu batas GKI + defconfig Pixel 6 — bukan akibat patch Avenia:

| Fitur DroidSpaces | Simbol | Status | Sebab |
|---|---|---|---|
| `--cpus` (batas CPU) | `CONFIG_CFS_BANDWIDTH` | tidak tersedia | menggeser ±4.000 CRC simbol ekspor → modul vendor prebuilt gagal load → bootloop |
| `--pids-limit` | `CONFIG_CGROUP_PIDS` | tidak tersedia | idem (struct cgroup) |
| limit memori / `memory.current` | `CONFIG_MEMCG` + `MEMCG_SWAP` | tidak tersedia | memang tidak ada di `raviole_defconfig` stok (walau `gki_defconfig` punya `MEMCG=y`) |

Namespace, IPC, devtmpfs, NAT/NAT66, UFW, fail2ban, dan overlay/tmpfs xattr **semua aktif**.
Rincian bukti + cara verifikasi: `DOKUMENTASI.md` §3.1–§3.3.

Konflik SUSFS: dokumen DroidSpaces menyebut "hide sus mounts for all processes" membuat container gagal boot.
Avenia mengatasinya lewat patch `9003` (exemption domain `u:r:droidspacesd:s0`); toggle tetap disarankan **OFF**.
