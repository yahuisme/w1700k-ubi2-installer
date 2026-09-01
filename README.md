# W1700K UBI Installer

用于 **Quantum Fiber / Gemtek W1700K** 的 OpenWrt 安装程序（基于 UBI），基于 [dangowrt/owrt-ubi-installer](https://github.com/dangowrt/owrt-ubi-installer) 等上游项目开发。

> ⚠️ **注意：** 安装程序会操作设备的 UBI 存储布局，错误操作可能导致设备无法启动，请确认了解安装流程后再操作。

## 安装流程

1. 安装 U-Boot Chainloader
2. 通过 TFTP 启动 UBI Installer
3. 运行 Installer 完成 OpenWrt 安装

### 1. 安装 U-Boot Chainloader

将电脑有线网卡 IP 设为 `192.168.1.10`，并在 TFTP 服务器提供：

```text
openwrt-airoha-an7581-gemtek_w1700k-ubi-chainload-uboot.itb
```

进入 W1700K 的 UART 控制台，执行：

```text
setenv serverip 192.168.1.10 ; setenv ipaddr 192.168.1.1 ; tftpboot 0x89000000 openwrt-airoha-an7581-gemtek_w1700k-ubi-chainload-uboot.itb
setenv one flash read 0x600000 0x100000 \$loadaddr
setenv two "; bootm"
setenv bootcmd "$one$two"
saveenv
flash erase 0x600000 0x100000
flash write 0x600000 0x100000 0x89000000
reset
```

设备重启后进入 **U-Boot Chainloader**。

### 2. 加载 UBI Installer

在 TFTP 服务器提供：

```text
openwrt-airoha-an7581-gemtek_w1700k-ubi-initramfs-installer.itb
```

设备重启进入 Chainloader 后，在启动菜单选择：

```text
4. Boot installer via TFTP.
```

### 3. 运行 Installer

若检测到已有 UBI 布局，Installer 会询问：

```text
Existing UBI layout detected. Proceed and overwrite? (yes/no)
```

确认重新安装请输入 `yes`（将格式化设备并覆盖现有数据），否则输入 `no`。

### 4. 等待安装完成

Installer 会自动完成 UBI 迁移并安装初始 OpenWrt，无需其它操作。安装完成并成功启动后，即可升级到自选的 W1700K 固件。

## 固件

日常升级固件**无需再次运行 Installer**，进入系统后直接使用固件自带升级方式（如 `sysupgrade`）即可。

提供两个系列固件（均含 `ubi2` 常规版与 `ubi2-oc` 超频版）：

| 固件 | 仓库 |
| --- | --- |
| OpenWrt | [w1700k-openwrt](https://github.com/yahuisme/w1700k-openwrt) |
| ImmortalWrt | [w1700k-immortalwrt](https://github.com/yahuisme/w1700k-immortalwrt) |

固件由 GitHub Actions 自动构建并发布在各仓库 Releases 页面，请确认下载的是适用于 W1700K 的 `ubi2` / `ubi2-oc` sysupgrade 镜像。

**内嵌初始固件：** `files/installer/` 下的 `openwrt-airoha-an7581-gemtek_w1700k-ubi-squashfs-sysupgrade.itb` 为 Installer 安装时写入的初始固件（当前为 2026.04.27 的 `ubi2` 构建）。如需让新安装设备直接获得最新固件，从上述任一仓库 Releases 下载对应 `ubi2` sysupgrade 镜像替换该文件，提交后重新运行构建工作流即可。

## 关于 Installer

用于 W1700K 首次安装 OpenWrt、UBI 存储布局初始化/迁移、系统重装与设备恢复。已正常运行 UBI2/OpenWrt 的设备无需为升级而重新运行本 Installer。

## 上游项目

* [dangowrt/owrt-ubi-installer](https://github.com/dangowrt/owrt-ubi-installer)
* [hurrian/w1700k-ubi-installer](https://github.com/hurrian/w1700k-ubi-installer)
* [w1700k/ubi2-installer](https://github.com/w1700k/ubi2-installer)

## 免责声明

刷写 U-Boot、修改 NAND/UBI 布局及安装固件均存在风险，请确保操作正确并了解相关风险。因操作错误、文件错误、断电等原因导致的设备损坏，由使用者自行承担。

## License

本项目遵循原项目所使用的开源许可证，详见仓库中的 `LICENSE` 文件。