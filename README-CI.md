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
├── .github/workflows/build-kernel.yml   ← workflow CI (sudah final)
├── patches/
│   ├── 9001-GKI-below-6.12-fix_sysvipc_kabi_6_7_8.patch   (kABI slot 6–8)
│   ├── 9002-DroidSpaces-raviole_defconfig.patch           (config namespace+IPC)
│   ├── 9003-exempt-droidspacesd-susfs.patch               (opsional: toggle susfs)
│   ├── 9004-avenia-rebrand.patch                          (rebrand: LOCALVERSION "-Avenia")
└── README-CI.md                          ← file ini
```

Catatan: `9001b` (fallback slot 1–3) sengaja TIDAK disertakan — itu hanya untuk
tree GKI standar, di tree staging ini dijamin gagal apply.

## 2. Langkah setup (tanpa terminal, ±5 menit)

1. **Buat repo baru** di akun GitHub Anda, mis. `gs101-droidspaces-build`
   (repository dapat private maupun public — public lebih aman soal kuota
   Actions gratis; private untuk repo publik kernel tetap dapat 2.000 menit/bulan).
2. **Upload isi folder ini** ke repo tersebut, jaga struktur foldernya:
   - Via web: add file → *Upload files* → drag folder yang berisi
     `.github/`, `patches/`, `README-CI.md`.
     > GitHub web tidak mengizinkan drag folder `.github` (diawali titik) —
     > solusi: upload lewat *Add file → Create new file*, ketik path
     > `.github/workflows/build-kernel.yml`, lalu paste isinya.
   - Atau via git biasa: `git init; git add .; git commit; git push`.
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
| Clone | kernel `staging` + `scripts` (build.sh) + KernelSU `fork` → `kernel/KernelSU` (posisi ini dihormati build.sh, tidak di-clone ulang) |
| Patch | `patch -p1` untuk keempat patch, berurutan |
| Brand Avenia | pre-clone AnyKernel3 (`Reinazhard/AnyKernel3`) → build.sh menghormati AK3 yang sudah ada; sed `kernel.string=Avenia Kernel by aryarifki` |
| Build | `CLANG_SOURCE=aosp` (prebuilt, jauh lebih cepat daripada klon LLVM kernel.org), `ZIPNAME=Avenia KSU=1 IS_RELEASE=1` → zip final jatuh di `kernel/AnyKernel3/*.zip` |
| Quality gate | assert semua config DroidSpaces `=y` di `out/.config` dan `CFS_BANDWIDTH`/`CGROUP_PIDS` tetap off — build dianggap gagal bila lolos |
| Artifact | zip AnyKernel3 (retensi 14 hari) + log gagal (3 hari) |

## 4. Build "otomatis" level berikutnya (opsional)

- **Build tiap kali patch berubah**: sudah aktif (trigger `push` pada `patches/**`).
- **Build terjadwal mengikuti upstream**: SUDAH AKTIF — cron `0 3 * * 1`
  (Senin 03:00 UTC / ±10:00 WIB), selalu memakai HEAD upstream saat clone
  (kernel staging, KernelSU fork, AnyKernel3, toolchain AOSP). Note: edit file
  workflow sendiri sengaja tidak lagi men-trigger build otomatis (perubahan
  patch saja yang men-trigger).
- **Release otomatis**: tambahkan step `softprops/action-gh-release` dengan
  `files: kernel/AnyKernel3/*.zip` + tag `refs/tags/v*`.

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
