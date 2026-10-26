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
| **ravindu644** | `droidspaces-oss` (app, dokumen `Kernel-Configuration.md`, patch kABI SYSVIPC) | Sumber requirement kernel yang diikuti patch 9001–9003; disinkronkan otomatis oleh workflow `sync-droidspaces` |
| **AOSP / Google** | prebuilt clang r614150 | Toolchain build (`CLANG_SOURCE=aosp`) |
| **aryarifki** | repo `Avenia-gs101` ini | Resep CI, patch 9004–9005 (identitas Avenia), dokumentasi & rilis |

Lisensi keseluruhan: **GPL-2.0** (pewarisan upstream). Kredit ini juga tercantum di README-CI
dan di body setiap rilis otomatis.

### Apa persisnya yang Avenia ubah dari upstream (transparansi mutlak)

Avenia memisahkan dua lapisan: **kompatibilitas DroidSpaces** (`9001`–`9003`, mengikuti rekomendasi resmi
DroidSpaces — bukan karya Avenia) dan **identitas** (`9004`–`9005`).

1. `9001` → kABI SYSVIPC dipindah ke slot padding `ANDROID_KABI_RESERVE(6..8)` (diadaptasi; lihat §3.1).
2. `9002` → menambah simbol defconfig untuk namespace/IPC/jaringan container (0 simbol dihapus).
3. `9003` → exemption domain `u:r:droidspacesd:s0` dari SUSFS mount-hiding (murni penambahan).
4. `9004` → `CONFIG_LOCALVERSION="-Avenia"` (1 baris defconfig — nama kernel).
5. `9005` → banner dmesg `Avenia Kernel by aryarifki || welcome to KernelSU …` (1 baris string `pr_info`).
6. `kernel.string` di anykernel.sh → `Avenia Kernel by aryarifki` (sed di CI, bukan patch source).
7. Nama zip/artifact/workflow → *Avenia*.

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
aryarifki/Avenia-gs101  (±100 KB — resep)
 ├── .github/workflows/build-kernel.yml     ← build + quality gate + rilis + changelog
 ├── .github/workflows/sync-droidspaces.yml ← sinkron requirement kernel DroidSpaces
 ├── .github/scripts/                       ← generator changelog & sync DroidSpaces
 ├── configs/droidspaces.requirements       ← 19 simbol GKI (auto-generated, jangan edit)
 ├── configs/droidspaces.source             ← pin SHA upstream DroidSpaces + hash patch
 ├── patches/9001…9005                      ← lapisan kompos
 ├── CHANGELOG.md                           ← akumulasi changelog (auto, per rilis)
 └── README-CI.md + DOKUMENTASI.md          ← dokumentasi

          └── saat CI jalan, runner meng-clone segar:
                ├─ https://github.com/Reinazhard/guacamole_sickness  @staging  → tree kernel utama
                ├─ https://github.com/Reinazhard/scripts                       → build.sh raviole
                ├─ https://github.com/Reinazhard/KernelSU            @fork     → kernel/KernelSU (driver root)
                └─ https://github.com/Reinazhard/AnyKernel3         @raviole  → kernel/AnyKernel3 (pembungkus zip)
```

Keuntungan pola ini: repo tetap kecil, HEAD upstream diikuti (rebuild mingguan otomatis),
tanpa beban merge pohon kernel ~2 GB. Sejak v2 keempat clone bisa **di-pin** per-run
(input `kernel_ref` / `ksu_ref` / `scripts_ref` / `ak3_ref`) untuk build reproducible
atau rollback ke HEAD yang terbukti hijau.

## 3. Stack patch 9001–9005

| # | Target | Makna |
|---|---|---|
| `9001` | kABI `sysvipc` slot 6–8 (GKI <6.12) | Menjaga layout struct IPC sesuai ekspektasi modul vendor (pengganti `9001b` slot 1–3 sengaja tidak dipakai — pasti gagal di tree ini) |
| `9002` | `raviole_defconfig` | Baseline namespace/IPC + fitur DroidSpaces. Sejak v2, requirement **dinamis** diambil dari `configs/droidspaces.requirements` (hasil sinkronisasi dokumen resmi DroidSpaces, 19 simbol) dan di-merge saat build — quality gate menegakkan semuanya `=y` |
| `9003` | Exempt daemon `droidspacesd` dari SUSFS | Daemon DroidSpaces melihat mount tree asli; root-hiding app lain tetap normal |
| `9004` | `CONFIG_LOCALVERSION` | `-86hm` → `-Avenia` (identitas kernel) |
| `9005` | `KernelSU/kernel/core/init.c` | Banner dmesg Avenia (string `pr_info`; `KSU_VERSION` & `KSU_PACKAGE_NAME` dijaga) |

### 3.1 Matriks fitur — apa yang ditambah, apa yang tidak tersedia

Pertanyaan yang sering muncul: *"konon kernel ini tidak bisa DroidSpaces karena tabrakan fitur — jadi fitur apa
yang dibuang?"* Jawabannya: **tidak ada fitur source yang dibuang.** Diff `raviole_defconfig` stok vs Avenia
= **0 baris dihapus**, kecuali string `LOCALVERSION` dan flip `UTS_NS`/`PID_NS` dari `not set` → `=y`.

| Metrik | Stok (`staging` 6.1.177) | Avenia (`9002`+`9004`) | Saat build (+ merge requirement) |
|---|---|---|---|
| Baris `CONFIG_` di `raviole_defconfig` | 723 | 739 | 744 |
| Baris dihapus | — | **0** | **0** |
| File kode sumber yang disentuh | — | 5 file | — |

Detail kelima patch (hasil hitung `+`/`-` langsung dari file patch):

| Patch | File | +/− | Sifat perubahan |
|---|---|---|---|
| `9001` | `include/linux/sched.h` | +10 / −5 | memindahkan `sysvsem`/`sysvshm` ke slot `ANDROID_KABI_RESERVE(6..8)` — **ukuran `task_struct` tidak berubah** |
| `9002` | `raviole_defconfig` | +20 / −2 | menambah simbol; "−2" = `LOCALVERSION` + flip `UTS_NS`/`PID_NS` |
| `9003` | `fs/namespace.c`, `KernelSU/kernel/selinux/selinux.c` | +28 / −0 | murni penambahan (exemption `droidspacesd`) |
| `9004` | `raviole_defconfig` | +2 / −2 | hanya string `LOCALVERSION` |
| `9005` | `KernelSU/kernel/core/init.c` | +1 / −1 | hanya string banner log |

#### Yang dihidupkan Avenia (di defconfig stok mati)

| Simbol | Stok | Avenia | Gunanya untuk DroidSpaces |
|---|---|---|---|
| `CONFIG_UTS_NS` | `# not set` | `=y` | hostname container |
| `CONFIG_PID_NS` | `# not set` | `=y` | PID namespace (init container = PID 1) |
| `CONFIG_SYSVIPC` + `CONFIG_POSIX_MQUEUE` | absen | `=y` | SysV/POSIX IPC (wajib patch `9001`) |
| `CONFIG_IPC_NS` + `CONFIG_USER_NS` | absen | `=y` | IPC & user namespace |
| `CONFIG_DEVTMPFS` | absen | `=y` | `/dev` di dalam container |
| `CONFIG_NETFILTER_ADVANCED` | absen | `=y` | membuka opsi XT (prasyarat NAT/UFW) |
| `CONFIG_NETFILTER_XT_MATCH_ADDRTYPE` | absen | `=y` | NAT keluar |
| `CONFIG_IP6_NF_NAT`, `CONFIG_IP6_NF_TARGET_MASQUERADE` | absen | `=y` | NAT IPv6 |
| `CONFIG_NETFILTER_XT_TARGET_REJECT/LOG`, `MATCH_RECENT` | absen | `=y` | UFW + fail2ban |
| `CONFIG_TMPFS_XATTR`, `CONFIG_TMPFS_POSIX_ACL` | absen | `=y` | xattr/ACL di tmpfs (rootfs NixOS) |
| `CONFIG_MACVLAN`, `CONFIG_IP_SET*`, `CONFIG_NETFILTER_XT_SET` | absen | `=y` (via `configs/droidspaces.requirements`) | jaringan container, UFW, fail2ban |

#### Yang tetap TIDAK tersedia — batas GKI, bukan keputusan Avenia

| Simbol | Fitur DroidSpaces yang hilang | Status di defconfig **stok** | Alasan tetap off |
|---|---|---|---|
| `CONFIG_CFS_BANDWIDTH` | `droidspaces --cpus`, batas CPU | **tidak ada** | mengubah ukuran struct scheduler → CRC ekspor bergeser (±4.000 simbol pada 5.15 menurut dokumen DroidSpaces) → modul vendor prebuilt gagal load → bootloop |
| `CONFIG_CGROUP_PIDS` | `--pids-limit` | **tidak ada** | idem (struct cgroup) |
| `CONFIG_MEMCG` + `MEMCG_SWAP` | limit memori, `memory.current` | **tidak ada** (walau `gki_defconfig` punya `MEMCG=y`) | pilihan defconfig Pixel 6 yang ramping, bukan akibat patch Avenia |

Konsekuensi praktis: container berjalan penuh, tetapi tiga jenis **limit** (CPU / memori / jumlah PID) dilewati.
Ini didokumentasikan DroidSpaces sendiri — `Documentation/Kernel-Configuration.md:252–262` mengomentari kedua
simbol, dan baris 287 menulis *"That limit is skipped."*

> **Kesimpulan:** Avenia bukan kernel "tanpa fitur". Ia kernel stok + namespace/IPC/jaringan container,
> minus tiga limit yang memang tidak mungkin ada di GKI tanpa memutus modul vendor.

### 3.2 "Tabrakan" yang dimaksud developer = SUSFS mount-hiding

Satu-satunya konflik yang terdokumentasi resmi ada di `droidspaces-oss/Documentation/Installation-Android.md:25`:

> *"SuSFS is not supported. If you use it anyway, turn off **'Hide sus mounts for all processes'** in its
> settings or containers will not boot, and do not report bugs seen with it enabled."*

Mekanisme: SUSFS menyembunyikan mount milik proses non-su, sedangkan container butuh melihat **mount tree asli**
→ rootfs tidak ditemukan → container gagal boot. Ini konflik *perilaku*, bukan fitur kernel yang dihapus.

`9003` mengecualikan domain `u:r:droidspacesd:s0` dari `susfs_get_non_sus_mnt_id`/`_mnt` (`fs/namespace.c`)
dan mendaftarkan SID-nya (`KernelSU/kernel/selinux/selinux.c`). Domain itu nyata — dipakai `src/daemon.c:923`
(`DS_SELINUX_CTX`) dan dideklarasikan permissive di `boot-module/sepolicy.rule` upstream. Hasilnya:

- daemon/kontainer DroidSpaces melihat mount tree asli;
- root-hiding untuk aplikasi lain tetap bekerja;
- default kernel ini: toggle SUSFS **OFF** (paling aman).

> Catatan jujur: exemption terikat pada **nama domain**. Jika upstream mengganti `droidspacesd`, patch tetap
> apply bersih tetapi tidak mengenai sasaran. Uji nyata: buat container dengan toggle hide-mounts ON; bila
> gagal boot, matikan toggle dan bandingkan `configs/droidspaces.source` (SHA upstream saat sinkronisasi).

### 3.3 Cara memverifikasi sendiri

```bash
# 1. tidak ada fitur yang dibuang: hitung baris '-' pada defconfig hasil patch
git -C kernel diff --stat -- arch/arm64/configs/raviole_defconfig

# 2. simbol yang dijanjikan benar-benar aktif di build
grep -E '^CONFIG_(SYSVIPC|IPC_NS|PID_NS|UTS_NS|MACVLAN|IP_SET)=' kernel/out/.config

# 3. batas ABI tetap terjaga (harus kosong)
grep -E '^CONFIG_(CFS_BANDWIDTH|CGROUP_PIDS)=y' kernel/out/.config

# 4. struct task_struct tidak berubah ukuran (offset sysvsem/sysvshm di padding)
grep -n 'ANDROID_KABI_USE(6' kernel/include/linux/sched.h
```

## 4. Pipeline CI — step-by-step

1. **Bebaskan disk** — buang SDK/.NET/CodeQL preinstalled (~+25 GB bebas).
2. **Dependencies host** — `bc bison build-essential cpio dwarves flex kmod libssl-dev libncurses-dev rsync wget zip`.
3. **Clone segar (opsional di-pin)** — tree staging + build.sh + fork + AK3 (§2). Token checkout
   tidak disimpan (job build hanya `contents: read`).
4. **Terapkan patch Avenia** — urut leksikografis `9001→9005` (`patch -p1 --forward`).
5. **Terapkan requirement DroidSpaces** — `configs/droidspaces.requirements` di-merge ke
   `raviole_defconfig` (append/ubah `# CONFIG_X is not set` → `=y`). Simbol
   `CFS_BANDWIDTH`/`CGROUP_PIDS` ditolak keras (merusak kABI vendor).
6. **Branding + guard AK3** — sed `kernel.string=Avenia Kernel by aryarifki`, lalu assert:
   device-check `oriole`/`raven`/`bluejay`, `do.devicecheck=1`, `do.modules=0`, `flash_generic dtbo`.
   Salah satu hilang dari AK3 upstream → build gagal (bukan flash diam-diam berbahaya).
7. **Build** — `CLANG_SOURCE=aosp IS_RELEASE=1 KSU=1 ZIPNAME=Avenia bash ../scripts/raviole/build.sh`
   → profil release (LTO + CFI/SCS aktif) → zip di `kernel/AnyKernel3/Avenia-gs101-ksu-release.zip`.
8. **Quality gate** — **semua** simbol requirement wajib `=y` di `out/.config`;
   `CFS_BANDWIDTH`/`CGROUP_PIDS` wajib off.
9. **Paket + metadata** — zip, `checksums.txt`, `meta.json` (SHA & tanggal upstream,
   versi SUSFS/KernelSU, clang, hash tiap patch, state DroidSpaces).
10. **Upload artifact** — retensi 14 hari; `build-log-failed` 3 hari hanya bila merah.
11. **Job rilis (terpisah, satu-satunya pemegang `contents: write`)** — susun changelog lengkap,
    cek duplikat sha256 terhadap rilis terakhir, buat tag `avenia-gs101-r<N>` + zip + checksums.
12. **Update `CHANGELOG.md` + `.upstream-state.json`** — commit oleh `github-actions[bot]`
    (`[skip ci]`), sehingga riwayat changelog menumpuk di repo, bukan hanya di halaman Releases.

Trigger: push `patches/**` atau `configs/**` • manual *Run workflow* (bisa pin ref + `force_release=1`)
• cron mingguan `0 3 * * 1` (Senin 03:00 UTC) • dispatch dari workflow `sync-droidspaces`.

### 4.1 Sinkronisasi DroidSpaces otomatis (workflow `sync-droidspaces`)

DroidSpaces **bukan** pohon kernel yang di-clone — ia app/CLI userspace. Yang dibutuhkan kernel
adalah (a) opsi config dan (b) patch kABI SYSVIPC. Keduanya dipublikasikan di
`ravindu644/droidspaces-oss`. Workflow harian (02:00 UTC) melakukan:

1. Clone `droidspaces-oss` @ HEAD.
2. Ekstrak daftar `CONFIG_*=y` dari section **GKI** di `Documentation/Kernel-Configuration.md`
   (anchor ke heading `## GKI kernels`, agar tidak tertukar dengan daftar non-GKI).
3. Tulis `configs/droidspaces.requirements` + `configs/droidspaces.source` (SHA upstream,
   hash dokumen, hash patch kABI, jumlah simbol).
4. Jika daftar berubah → commit + `gh workflow run build-kernel.yml` (build & rilis otomatis).
5. Jika **patch kABI upstream berubah** → buka **Issue** (tidak menimpa otomatis), karena
   `patches/9001` di repo ini diadaptasi ke slot padding **6–8** (slot 1–3 sudah terpakai di
   tree `guacamole_sickness`). Menimpanya buta bisa menggeser offset struct vendor → bootloop.

Artinya: pembaruan DroidSpaces terdeteksi maksimal 24 jam, dan build baru berjalan hanya bila
requirement benar-benar berubah (bukan rebuild harian yang membuang menit runner).

### 4.2 Changelog lengkap & anti-rilis-duplikat

Setiap rilis memuat: tabel perubahan SHA upstream (kernel/fork/scripts/AK3) + **judul commit**
dari GitHub Compare API, daftar commit repo sejak tag sebelumnya, identitas kernel
(`uname -r`, SUSFS, KernelSU, clang), patch stack + sha256, state DroidSpaces, langkah
verifikasi, dan checksum. Zip yang **byte-identik** dengan rilis terakhir tidak membuat rilis
baru (artifact tetap dipertahankan); override dengan `force_release=1`.

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
   Jika Anda menyalakan **"Hide sus mounts for all processes"**, container DroidSpaces tetap bisa boot berkat
   `9003` (domain `droidspacesd` dikecualikan) — tetapi default yang disarankan tetap **OFF** (§3.2).

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
  Baca juga §3.1: `--cpus`/`--pids-limit`/limit memori memang **tidak akan pernah** PASS di kernel ini
  (batas kABI). Yang wajib PASS adalah namespace/IPC/jaringan — bila salah satunya merah, itu bug CI.
- **Container gagal boot padahal namespace/IPC PASS** → cek toggle SUSFS "hide sus mounts for all
  processes". Dengan `9003` seharusnya tetap jalan; bila tidak, domain `droidspacesd` berubah di upstream
  (lihat §3.2) — matikan toggle, lalu buka Issue dari workflow `sync-droidspaces`.
- **Rilis tidak muncul padahal build hijau** → zip byte-identik dengan rilis terakhir (anti-duplikat, §4.2).
  Jalankan manual dengan `force_release=1` bila tetap ingin menerbitkan.
- **`sync-droidspaces` merah** → biasanya format dokumen upstream berubah (anchor `## GKI kernels` /
  `### Step 2` hilang). Skrip sengaja gagal keras, bukan menulis requirement kosong.

## 9. Roadmap opsional

- Bernalah bertahap: branding semakin dalam (string internal fork) = patch kecil saat berminat.
- `prerelease: true` bisa ditambahkan di step rilis untuk build eksperimen (debug flag).
- Broaden multi-device ala GKID (matrix 5 KMI) akan kehilangan ketegasan device-matched —
  tidak direkomendasikan untuk pemegang perangkat tunggal.

## 10. Glosarium

- **GKI** — Generic Kernel Image; inti kernel standar Android, bagian device-spesifik hidup di modul vendor.
- **KMI** — Kernel Module Interface; kontrak ABI antar modul vendor (contoh band: `android14-6.1`).
- **kABI padding** — slot cadangan (`ANDROID_KABI_RESERVE`) di struct inti yang sengaja disediakan Google;
  `9001` memakainya agar `CONFIG_SYSVIPC` aktif tanpa menggeser offset field yang dibaca modul vendor.
- **DroidSpaces** — runtime container Android (app + CLI + daemon `droidspacesd`); butuh namespace, IPC,
  devtmpfs, dan aturan SELinux — bukan pohon kernel, sehingga "pembaruan"-nya berarti pembaruan *requirement*.
- **Requirement DroidSpaces** — daftar `CONFIG_*=y` hasil ekstraksi dokumen resmi, disimpan di
  `configs/droidspaces.requirements` dan di-merge saat build (§4.1).
- **SUSFS** — lapisan kernel untuk root-hiding (hide mounts/paths untuk procs non-su) oleh simonpunk.
- **AK3 / AnyKernel3** — framework zip flashable universal (repack boot.img di recovery).
- **Artifact vs Release** — artifact = penyimpanan sementara hasil build (14 hari); Release = halaman publik permanen + asset.

---

*Repo: `aryarifki/Avenia-gs101` — disusun 2026-10-22, diperbarui 2026-10-26 (pipeline v2 + matriks fitur §3.1)
terhadap tree `guacamole_sickness@staging` 6.1.177.*
