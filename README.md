# W1700K UBI Installer

用于 Gemtek W1700K 安装 OpenWrt UBI2。

> ⚠️ 刷写 U-Boot / NAND 存储存在变砖风险，请确认设备型号和固件正确。刷写过程中不要断电。

## 1. 准备

需要：

* W1700K
* USB-TTL（3.3V TTL）
* 网线
* Windows PC
* [PuTTY](https://www.putty.org/)
* [Tftpd64](https://bitbucket.org/phjounin/tftpd64/wiki/Home)

准备好以下两个文件，并放到同一个 TFTP 文件夹，例如：

```text
C:\tftp\
├── openwrt-airoha-an7581-gemtek_w1700k-ubi-chainload-uboot.itb
└── openwrt-airoha-an7581-gemtek_w1700k-ubi-initramfs-installer.itb
```

---

## 2. USB-TTL 接线

**W1700K 网口朝向自己时，UART 从左到右：**

```text
1    2     3     4     5
TX   GND   VCC   N/A   RX
```

连接 USB-TTL：

```text
W1700K TX  → TTL RX
W1700K GND → TTL GND
W1700K RX  → TTL TX
```

**VCC 不要连接。**

> 必须使用 3.3V TTL，不能使用 RS-232。
> TX/RX 需要交叉连接。

---

## 3. PuTTY 设置

插入 USB-TTL 后，在 Windows「设备管理器 → 端口」查看 COM 端口。

PuTTY 选择：

```text
Connection type: Serial
Serial line: COMx
Speed: 115200
```

Serial 设置：

```text
Data bits: 8
Stop bits: 1
Parity: None
Flow control: None
```

打开串口后再给 W1700K 通电。

---

## 4. 设置电脑 IP

电脑通过**网线直接连接 W1700K LAN 口**。

将 Windows 有线网卡 IPv4 设置为：

```text
IP address:   192.168.1.10
Subnet mask:  255.255.255.0
Gateway:      留空
DNS:          留空
```

刷机过程中建议暂时关闭 Wi-Fi、VPN 和其它虚拟网卡。

---

## 5. Tftpd64 设置

打开 Tftpd64：

```text
Current Directory:
C:\tftp
```

`Server interfaces` 选择：

```text
192.168.1.10
```

不要选择 `127.0.0.1` 或其它网卡。

如果 Windows 防火墙弹出提示，请允许 Tftpd64 通过**专用网络**。

---

## 6. 刷写 U-Boot Chainloader

给 W1700K 通电。

PuTTY 应该开始出现类似：

```text
U-Boot ...
...
Hit any key to stop autoboot:
```

看到：

```text
Hit any key to stop autoboot
```

的时候，马上按几下 Enter 或空格。

最终应该停在类似：

```text
U-Boot>
```

复制以下命令行执行：

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

重启后应进入 U-Boot 菜单。

---

## 7. 启动 UBI Installer

确认 Tftpd64 中仍然存在：

```text
openwrt-airoha-an7581-gemtek_w1700k-ubi-initramfs-installer.itb
```

在 U-Boot 菜单选择：

```text
4. Boot installer via TFTP
```

Installer 启动后，根据提示操作。

如果提示已有 UBI 布局并询问是否覆盖：

```text
Existing UBI layout detected.
Proceed and overwrite? (yes/no)
```

如果确认要重新安装，输入：

```text
yes
```

然后等待 Installer 完成。

> ⚠️ Installer 执行 NAND/UBI 操作时可能会出现一段时间没有输出。
> **不要因为暂时没有输出就立即断电。**

---

## 8. 常见问题

### PuTTY 没有任何输出

检查：

* COM 端口是否正确
* Baud rate 是否为 `115200`
* Flow control 是否为 `None`
* TX/RX 是否交叉连接
* GND 是否连接
* USB-TTL 是否为 3.3V TTL

### TFTP 下载失败

检查：

```text
PC IP          = 192.168.1.10
Tftpd interface = 192.168.1.10
Current Directory = 正确文件夹
文件名          = 完全正确
```

同时检查 Windows 防火墙。

### 菜单 4 后长时间没有明显变化

菜单 4 会先通过 TFTP 下载 Installer，然后才启动 Installer。

可以观察 Tftpd64 是否收到文件请求，以及 PuTTY 是否继续输出日志。不要在没有确认失败之前断电。

---

## 9. 参考

* [OpenWrt W1700K Device Page](https://openwrt.org/toh/gemtek/mxf-w1700k)
* [W1700K UBI2 Installer](https://github.com/yahuisme/w1700k-ubi2-installer)
