# Build Otomatis 86hm-gs101 + DroidSpaces via GitHub Actions

> Jawaban singkat: **TIDAK harus dari terminal ini.** Cara paling praktis = GitHub
> Actions (gratis, tidak makan disk lokal, tidak perlu toolchain lokal). Build
> dari terminal (proot Android) tetap *mungkin*, tapi butuh ±40 GB disk + beberapa
> jam + unduhan toolchain besar — tidak disarankan.

---

## 1. Isi folder `github-ci/`

```
github-ci/
├── .github/workflows/build-kernel.yml   ← workflow CI (sudah final)
├── patches/
│   ├── 9001-GKI-below-6.12-fix_sysvipc_kabi_6_7_8.patch   (kABI slot 6–8)
│   ├── 9002-DroidSpaces-raviole_defconfig.patch           (config namespace+IPC)
│   ├── 9003-exempt-droidspacesd-susfs.patch               (opsional: toggle susfs)
│   ├── 9004-avenia-rebrand.patch                          (banner uname -r: versi-avenia)
│   └── 9005-avenia-ksu-susfs-port.patch                   (port SUSFS v2.3.0 ke fork backslashxx)
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
5. Unduh artifact **`avenia-gs101-ksu-release-droidspaces`** → flash via
   Recovery/TWRP biasa. Nama zip: `Avenia-gs101-ksu-release.zip`.

## 3. Apa yang dilakukan workflow (otomatis, sudah sesuai hasil analisis)

| Step | Detail |
|---|---|
| Bebaskan disk | hapus SDK Android/.NET/CodeQL preinstalled runner (~+25 GB) |
| Deps host | `bc bison flex cpio dwarves(pahole) libssl-dev kmod rsync zip` |
| Clone | kernel `staging` + `scripts` (build.sh) + KernelSU fork **backslashxx@master** → `kernel/KernelSU` (posisi ini dihormati build.sh, tidak di-clone ulang) |
| AnyKernel3 | pre-clone `Reinazhard/AnyKernel3` sebelum build (dihormati build.sh) + `sed` `kernel.string` → `Avenia Kernel by reinazhard (86hm)` |
| Patch | `patch -p1` untuk kelima patch, berurutan (9005 menyediakan shim/hook yang dibinding call-site staging) |
| Build | `CLANG_SOURCE=aosp` (prebuilt, jauh lebih cepat daripada klon LLVM kernel.org), `ZIPNAME=Avenia KSU=1 IS_RELEASE=1` → zip final jatuh di `kernel/AnyKernel3/*.zip` |
| Quality gate | assert configs DroidSpaces `=y` + 9 config `CONFIG_KSU(_SUSFS*)=y` di `out/.config`; negatif: `CFS_BANDWIDTH`/`CGROUP_PIDS` serta `KSU_TAMPER_SYSCALL_TABLE`/`KSU_HACK_ARM64_BRANCH_LINK` wajib off |
| Identitas Avenia | zip `Avenia-gs101-ksu-release.zip`, banner `uname -r` di-rebrand ke `-avenia`, kredit sumber tetap: 86hm/reinazhard, backslashxx/SukiSU, susfs4ksu/simonpunk |
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
   CLANG_SOURCE=aosp IS_RELEASE=1 KSU=1 bash ../scripts/raviole/build.sh
   ```
4. Ekspektasi: banyak lebih lambat daripada runner CI, dan proot bisa rewel soal
   memori saat LTO (butuh swap besar). Ini urusan ±6–12 jam di ponsel/typan.

## 6. Jaga-jaga

- Jika 9001 memicu bootloop (offset kABI) → ganti patch 9001 dengan paket
  fallback `3_4_5` (URL ada di bundle `droidspaces-oriole/README-BUILD-ORIOLE.md`), commit,
  push → CI rebuild otomatis.
- Jika `Check Requirements` di app DroidSpaces masih menolak → kirim log
  `build.log` + `out/.config` (artifact) untuk kami diagnosa.
