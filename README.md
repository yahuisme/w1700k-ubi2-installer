# W1700K UBI Installer

用于 **Quantum Fiber / Gemtek W1700K** 的 OpenWrt 固件安装程序（基于 UBI）。

本项目基于 [dangowrt/owrt-ubi-installer](https://github.com/dangowrt/owrt-ubi-installer) 开发。

> **注意：** 本安装程序会对设备的 UBI 存储布局进行操作。请在确认自己了解安装流程后再进行操作。错误的操作可能导致设备无法正常启动。


## 安装流程

整个安装过程分为以下三个步骤：

1. 安装 U-Boot Chainloader
2. 通过 TFTP 启动 W1700K UBI Installer
3. 运行 UBI Installer 并完成 OpenWrt 安装


## 1. 安装 U-Boot Chainloader

首先，将电脑的有线网卡 IP 地址设置为：

```text
192.168.1.10
```

确保你的 TFTP 服务器正在提供以下 U-Boot Chainloader 文件：

```text
openwrt-airoha-an7581-gemtek_w1700k-ubi-chainload-uboot.itb
```

然后进入 W1700K 的 UART 控制台，输入以下命令：

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

设备随后会重新启动并进入 **U-Boot Chainloader**。


## 2. 加载 W1700K UBI Installer

在你的 TFTP 服务器中提供以下 Installer 文件：

```text
openwrt-airoha-an7581-gemtek_w1700k-ubi-initramfs-installer.itb
```

设备重新启动进入 U-Boot Chainloader 后，会显示类似下面的启动菜单：

```text
 *** U-Boot Boot Menu ***

      1. Run default boot command.
      2. Boot system via TFTP.
      3. Boot recovery system from flash.
      4. Boot installer via TFTP. <---------------- SELECT THIS
      5. Reboot.
      0. Exit
```

选择：

```text
4. Boot installer via TFTP.
```


## 3. 运行 W1700K UBI Installer

如果设备之前已经安装过 OpenWrt，Installer 可能会检测到现有的 UBI 存储布局，并询问：

```text
Existing UBI layout detected. Proceed and overwrite? (yes/no)
```

如果确认继续安装，请输入：

```text
yes
```

> ⚠️ **警告：** 输入 `yes` 后，Installer 将继续执行设备重新格式化操作。

这可能会覆盖设备现有的系统数据和 UBI 存储布局。

如果不确定是否应该继续，请输入：

```text
no
```


## 4. 等待安装完成

Installer 启动后，无需进行其他操作，只需要等待安装程序完成。

Installer 会自动执行必要的 UBI 迁移，并为 W1700K 安装一个初始版本的 OpenWrt。

安装完成并成功启动后，即可继续升级到自己选择的 OpenWrt 固件。


# 固件下载

如果你希望直接使用我构建的 W1700K OpenWrt 固件，可以访问：

**[yahuisme/w1700k-openwrt](https://github.com/yahuisme/w1700k-openwrt)**

该项目基于 W1700K OpenWrt 构建项目进行定制，加入中文和主题以及其它易用性支持，并通过 GitHub Actions 自动构建固件。

目前提供：

* `ubi2`
* `ubi2-oc`

等 W1700K 固件构建版本。

固件会通过 GitHub Actions 自动构建，并发布到该项目的 Releases 页面。

👉 **[下载 W1700K OpenWrt 固件](https://github.com/yahuisme/w1700k-openwrt/releases)**


## 固件升级说明

完成 UBI Installer 安装并成功进入 OpenWrt 后，**日常升级固件不需要再次运行 UBI Installer**。

后续可以直接使用对应固件提供的正常升级方式。

例如使用：

```text
sysupgrade
```

进行系统升级。

> **请务必确认所使用的固件适用于 Quantum Fiber / Gemtek W1700K，并选择正确的固件类型。**


## 关于 UBI Installer

本项目主要用于：

* W1700K 首次安装 OpenWrt
* UBI 存储布局初始化
* UBI 存储布局迁移
* OpenWrt 系统重新安装
* 设备恢复

如果你的 W1700K 已经正常运行 UBI2/OpenWrt，**没有必要为了升级系统而重新运行本 Installer。**


## 文件说明

### U-Boot Chainloader

```text
openwrt-airoha-an7581-gemtek_w1700k-ubi-chainload-uboot.itb
```

用于将 U-Boot Chainloader 写入设备。

### UBI Installer

```text
openwrt-airoha-an7581-gemtek_w1700k-ubi-initramfs-installer.itb
```

用于通过 TFTP 启动 UBI Installer，并执行 UBI 存储布局初始化/迁移以及 OpenWrt 安装。

### 内嵌固件载荷

`files/installer/` 下的 `openwrt-airoha-an7581-gemtek_w1700k-ubi-squashfs-sysupgrade.itb` 是手动注入的初始 OpenWrt 固件（当前为 2026.04.27 的 `ubi2` 构建），Installer 安装时会将其写入设备。

W1700K 固件发布新版本后，如需让新安装的设备直接获得最新固件，请从 [w1700k-openwrt Releases](https://github.com/yahuisme/w1700k-openwrt/releases) 下载对应 `ubi2` 的 sysupgrade 镜像替换该文件，提交后重新运行构建工作流即可。


## 上游项目

本项目基于以下开源项目：

* [dangowrt/owrt-ubi-installer](https://github.com/dangowrt/owrt-ubi-installer)
* [hurrian/w1700k-ubi-installer](https://github.com/hurrian/w1700k-ubi-installer)
* [w1700k/ubi2-installer](https://github.com/w1700k/ubi2-installer)


## 免责声明

刷写 U-Boot、修改 NAND/UBI 存储布局以及安装 OpenWrt 均存在一定风险。

请确保：

* 正确连接 UART
* 正确配置 TFTP 服务器
* 使用正确的文件
* 确认设备型号兼容
* 在操作前了解相关风险

因刷写过程中操作错误、文件错误、断电或其他原因导致的设备损坏，由使用者自行承担责任。


## License

本项目遵循原项目所使用的开源许可证。

详细信息请参阅仓库中的 `LICENSE` 文件。
