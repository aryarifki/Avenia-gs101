<p align="center">
  <img src="assets/Hamsa.svg" alt="Avenia Kernel Banner" width="100%" />
</p>

<h1 align="center">Avenia Kernel (gs101)</h1>

<p align="center">
  <b>High-Performance, Stealth-Rooted, Container-Ready Android Kernel for Google Pixel 6 Series (GS101)</b>
</p>

<p align="center">
  <a href="https://github.com/aryarifki/Avenia-gs101/actions"><img src="https://img.shields.io/github/actions/workflow/status/aryarifki/Avenia-gs101/build-kernel.yml?branch=main&label=Build%20CI&logo=github&style=flat-square" alt="CI Status" /></a>
  <a href="https://github.com/aryarifki/Avenia-gs101/releases"><img src="https://img.shields.io/github/v/release/aryarifki/Avenia-gs101?color=blue&label=Latest%20Release&logo=android&style=flat-square" alt="Latest Release" /></a>
  <a href="https://source.android.com/"><img src="https://img.shields.io/badge/Android%20ACK-6.1%20LTS-brightgreen?style=flat-square&logo=linux" alt="Kernel Version" /></a>
  <a href="https://kernelsu.org/"><img src="https://img.shields.io/badge/KernelSU-v3.0.0%2B%20(v32680)-orange?style=flat-square" alt="KernelSU" /></a>
  <a href="https://gitlab.com/simonpunk/susfs4ksu"><img src="https://img.shields.io/badge/SUSFS-v2.3%20Integrated-purple?style=flat-square" alt="SUSFS" /></a>
  <a href="https://github.com/ravindu644/droidspaces-oss"><img src="https://img.shields.io/badge/DroidSpaces-Container%20Ready-teal?style=flat-square" alt="DroidSpaces Ready" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-GPL--2.0-yellow?style=flat-square" alt="License" /></a>
</p>

---

## 📖 Overview

**Avenia Kernel** is an advanced, custom-tailored Android kernel distribution specifically designed for the **Google Tensor GS101** platform powering the Google Pixel 6 series. Built on the upstream `android14-6.1` LTS tree, Avenia blends uncompromising system responsiveness and military-grade compiler hardening with seamless next-generation root management (**KernelSU**), deep kernel-level anti-detection filesystem stealth (**SUSFS**), and full Linux container virtualization compatibility (**DroidSpaces**).

Instead of maintaining a multi-gigabyte monolithic fork, `Avenia-gs101` implements an elegant, modular **recipe-based CI architecture**. Automated GitHub Actions workflows pull upstream source trees at build time, apply precise kABI-safe patches, configure optimal device-specific parameters, and produce signed, flashable [AnyKernel3](https://github.com/osm0sis/AnyKernel3) release packages.

---

## 📱 Supported Devices

Avenia Kernel targets Google's first-generation Tensor SoC (**GS101** / platform codename `raviole`):

| Device Model | Codename | Platform / SoC | Supported Android Versions | AnyKernel3 Check |
| :--- | :--- | :--- | :--- | :---: |
| **Google Pixel 6** | `oriole` | Google Tensor GS101 | Android 14 / 15 / 16 / 17 | ✅ Verified |
| **Google Pixel 6 Pro** | `raven` | Google Tensor GS101 | Android 14 / 15 / 16 / 17 | ✅ Verified |
| **Google Pixel 6a** | `bluejay` | Google Tensor GS101 | Android 14 / 15 / 16 / 17 | ✅ Verified |

> [!NOTE]
> Flashing is protected by device safety checks within `anykernel.sh`. Attempting to flash onto unsupported hardware will abort cleanly without modifying boot partitions.

---

## ⚙️ Technical Specifications

```ini
[Kernel Information]
Distribution    = Avenia Kernel by aryarifki
Repository      = https://github.com/aryarifki/Avenia-gs101
Target SoC      = Google Tensor GS101 (2x Cortex-X1 @ 2.80GHz, 2x Cortex-A76 @ 2.25GHz, 4x Cortex-A55 @ 1.80GHz)
Architecture    = aarch64 (ARM64)
Base Tree       = android14-6.1 Common Kernel (ACK / GKI 2.0)
Kernel Version  = Linux 6.1.176 / 6.1.177 LTS
Localversion    = -Avenia (e.g., 6.1.177-rel6-Avenia-ybrt)
Toolchain       = AOSP Prebuilt Clang (r614150 / Clang 23.x / LLD)
Security Engine = Forward-Edge CFI + Shadow Call Stack (SCS) + Thin-LTO
Defconfig Base  = arch/arm64/configs/raviole_defconfig
Packaging       = AnyKernel3 (flashes boot, vendor_boot, and dtbo)
```

### Core Security & Hardening Features
- **Control Flow Integrity (CFI)**: Fully compiled with `CONFIG_CFI_CLANG=y` to prevent forward-edge code reuse and return-oriented exploits.
- **Shadow Call Stack (SCS)**: Armed with `CONFIG_SHADOW_CALL_STACK=y` to prevent return address tampering on ARM64 architectures.
- **Link-Time Optimization (LTO)**: Compiled under `CONFIG_LTO_CLANG_THIN=y` for cross-module function inlining, reduced kernel footprint, and superior execution branch prediction.
- **Preemption Model**: `CONFIG_PREEMPT=y` (SMP PREEMPT) ensuring low system latency and smooth frame pacing.

---

## ✨ Features & Advantages

### 🛡️ 1. In-Tree KernelSU (Fork v3.0.0+ / Version 32680)
- **Native Kernel Driver**: KernelSU is integrated directly into the kernel core rather than loaded as a delayed loadable module, ensuring immediate root readiness upon early boot.
- **Full Architecture Support**: Complete feature handlers including `sucompat`, `adb_root`, `sulog`, `selinux_hide`, and non-blocking file descriptor wrappers (`ksu_wrapper_*`).
- **Standard Ecosystem Compatibility**: Works out of the box with the official KernelSU manager application (`me.weishu.kernelsu`).

### 👻 2. Complete SUSFS Integration (Kernel-Level Stealth)
- **Mount & Path Concealment**: Employs `sus_path` and `sus_mount` hooks to prevent detection of rooted filesystems, binaries, and temporary mount overlays.
- **Spoofing Suite**: Integrated `sus_kstat` spoofing for `vfs_statfs`, `show_map_vma`, `proc_fd_seq`, and `inotify_fdinfo`, as well as `uname` and `avc_log` spoofing.
- **Open-Redirect & SDCard Monitor**: Advanced FUSE redirection and continuous sdcard monitoring (`susfs_sdcard_monitor`) to seamlessly bypass banking app protections, root detectors, and Play Integrity checks.

### 🐧 3. Native DroidSpaces Container Support (Zero kABI Breakage)
- **Custom kABI Padding Alignment ([Patch 9001](patches/9001-GKI-below-6.12-fix_sysvipc_kabi_6_7_8.patch))**: 
  Unlike standard ACK kernels where enabling IPC namespaces alters `task_struct` offsets and breaks vendor binary modules (camera, modem, GPU drivers), Avenia introduces a specialized kABI fix utilizing free padding slots (slots 6–8) in `task_struct` (`include/linux/sched.h`).
- **Complete Virtualization & Namespace Suite ([Patch 9002](patches/9002-DroidSpaces-raviole_defconfig.patch))**:
  Full support for Linux userland containers:
  `CONFIG_UTS_NS=y`, `CONFIG_PID_NS=y`, `CONFIG_IPC_NS=y`, `CONFIG_SYSVIPC=y`, `CONFIG_POSIX_MQUEUE=y`, `CONFIG_USER_NS=y`, `CONFIG_DEVTMPFS=y`, `CONFIG_NETFILTER_ADVANCED=y`, `CONFIG_IP6_NF_NAT=y`, `CONFIG_TMPFS_POSIX_ACL=y`.
- **SUSFS Daemon Coexistence ([Patch 9003](patches/9003-exempt-droidspacesd-susfs.patch))**:
  Exempts the `droidspacesd` daemon from mount-hiding isolation. You can safely activate root hiding and containerized Linux distributions (Debian, Arch Linux, Alpine, Ubuntu) simultaneously without mount visibility collisions.

### ⚡ 4. Modern Networking & Virtualization
- **In-Kernel WireGuard**: `CONFIG_WIREGUARD=y` for fast, efficient, battery-friendly encrypted VPN tunneling at wire speed.
- **Kernel-based Virtual Machine (KVM)**: `CONFIG_KVM=y` fully enabled for native virtualization tasks and developer sandboxes.

---

## 🧩 Patch Architecture

The kernel image is assembled via modular, layered patches applied on top of the upstream staging tree:

```
Avenia-gs101/
├── .github/workflows/build-kernel.yml       # Automated CI pipeline & release engine
├── assets/Hamsa.svg                         # Repository visual identity
├── patches/
│   ├── 9001-GKI-below-6.12-fix_sysvipc_kabi_6_7_8.patch  # kABI safe IPC for task_struct (slots 6-8)
│   ├── 9002-DroidSpaces-raviole_defconfig.patch          # Namespaces, IPC, Devtmpfs, ACL defconfig
│   ├── 9003-exempt-droidspacesd-susfs.patch              # Exemption for DroidSpaces daemon in SUSFS
│   ├── 9004-avenia-rebrand.patch                         # Kernel localversion rebrand (-Avenia)
│   └── 9005-avenia-ksu-brand.patch                       # Kernel boot dmesg branding
└── README.md
```

---

## 🚀 Installation Guide

### Prerequisites
1. An unlocked bootloader on Google Pixel 6 (`oriole`), Pixel 6 Pro (`raven`), or Pixel 6a (`bluejay`).
2. Current firmware running Android 14, 15, or 16.
3. A custom recovery (TWRP / LineageOS Recovery) or an authorized kernel manager application capable of AnyKernel3 flashing.
4. **Mandatory Step**: Backup your existing `boot`, `vendor_boot`, and `dtbo` partitions before flashing!

### Flashing via Custom Recovery
1. Download the latest `Avenia-gs101-ksu-release.zip` from the [Releases](https://github.com/aryarifki/Avenia-gs101/releases) page.
2. Verify the SHA-256 checksum:
   ```bash
   sha256sum Avenia-gs101-ksu-release.zip
   ```
3. Transfer the zip to your device:
   ```bash
   adb push Avenia-gs101-ksu-release.zip /sdcard/Download/
   ```
4. Reboot into Recovery mode:
   ```bash
   adb reboot recovery
   ```
5. In recovery, select **Apply update** &rarr; **Choose from internal storage** &rarr; select `Avenia-gs101-ksu-release.zip`.
6. Confirm the flash. The AnyKernel3 installer will automatically backup ramdisk items, split the boot image, patch the kernel payload, and flash `boot`, `vendor_boot`, and `dtbo`.
7. Reboot the system.

### Verification After Boot
Open a root terminal or run via `adb shell`:

```bash
# 1. Verify kernel release string
uname -r
# Expected output contains: -Avenia

# 2. Inspect kernel boot banner in dmesg
dmesg | grep "Avenia Kernel"
# Expected output:
# Avenia Kernel by aryarifki || welcome to KernelSU version 32680, package name me.weishu.kernelsu

# 3. Check DroidSpaces requirements
# Launch the DroidSpaces app -> Settings -> Requirements -> Check Requirements
# All essential namespaces (PID, IPC, UTS, Mount) will report PASSED!
```

---

## 🛠️ Automated CI/CD Pipeline

Builds are powered by GitHub Actions (`ubuntu-24.04`), ensuring reproducibility and clean compilation:

- **Trigger Mechanisms**:
  - **Push**: Automatically triggers when modifications are pushed to `patches/**`.
  - **Weekly Cron**: Triggers every Monday at 03:00 UTC (`0 3 * * 1`) to compile against the freshest upstream ACK and toolchain commits.
  - **Manual Dispatch**: Triggered on-demand with configurable release flags.
- **Quality Gate**:
  - Automatically verifies that all 13 critical container flags (`CONFIG_UTS_NS`, `CONFIG_PID_NS`, `CONFIG_SYSVIPC`, etc.) are asserted `=y`.
  - Enforces vendor ABI stability by verifying that unstable scheduler flags (`CONFIG_CFS_BANDWIDTH` and `CONFIG_CGROUP_PIDS`) remain disabled.

---

## 🤝 Credits & Acknowledgements

Avenia Kernel is built upon the dedicated work of the open-source Android and Linux kernel engineering communities. Deep gratitude and first-hand attribution go to:

- **[Reinazhard](https://github.com/Reinazhard)**:
  - Developer of the `guacamole_sickness` kernel source tree (branch `staging`), providing exceptional GS101 tuning, staging fixes, and kABI slot layouts.
  - Maintainer of the enhanced `KernelSU` fork with native built-in SUSFS integration.
  - Creator of the raviole compilation toolchain scripts and AnyKernel3 deployment orchestration.
- **[simonpunk](https://gitlab.com/simonpunk)**:
  - Author and architect of **SUSFS** (`susfs4ksu`), setting the gold standard for kernel-level anti-detection, path concealment, and filesystem isolation.
- **[tiann (Weishu)](https://github.com/tiann)** & **KernelSU Team**:
  - Creators and maintainers of the revolutionary [KernelSU](https://github.com/tiann/KernelSU) project, providing an elegant, kernel-based privilege elevation paradigm.
- **[osm0sis](https://github.com/osm0sis)**:
  - Developer of [AnyKernel3](https://github.com/osm0sis/AnyKernel3), the quintessential universal ramdisk modifying and kernel deployment framework for Android devices.
- **[Ravindu644](https://github.com/ravindu644) & The DroidSpaces Team**:
  - Developers of [DroidSpaces](https://github.com/ravindu644/droidspaces-oss), enabling true containerized GNU/Linux environments on Android, and authors of the upstream GKI kABI compatibility guidelines.
- **Google & The Android Open Source Project (AOSP)**:
  - For the Android Common Kernel (ACK) codebase, Tensor GS101 platform documentation, and prebuilt Clang/LLVM toolchains.
- **[aryarifki](https://github.com/aryarifki)**:
  - Maintainer of the `Avenia-gs101` project, customized kABI slot 6–8 integration, DroidSpaces SUSFS exemption layer, CI/CD automated pipeline, and release lifecycle.

---

## 📜 License

This project is licensed under the **GNU General Public License v2.0** ([GPL-2.0](LICENSE)) in accordance with the Linux kernel upstream licensing requirements.
