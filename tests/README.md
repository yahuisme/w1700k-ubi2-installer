# 本地测试

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
busybox ash -n files/installer/install.sh
busybox ash -n files/lib/preinit/00_installer
git diff --check
```

工作流回放测试需要 Python 3、PyYAML 和 `rsync`。发布检查与清理均使用私有 `gh` 替身，不访问或修改 GitHub Release；已有同名 Release 会阻止重跑覆盖，需通过新的 workflow dispatch 生成新编号。

运行 `test_installer.py` 需要 Linux、root（chroot）、`/usr/bin/busybox`、`ldd`，并设置 `TMPDIR` 到可写临时目录。每例创建并清理独立 chroot，复制 BusyBox 与动态库，不挂载宿主 `/dev`、`/sys`、`/proc`；硬件命令、sync、sleep、reboot 均为 stub。普通文件模拟原厂数据及 UBI 卷。多数故障注入使用助手替身；`test_real_helpers_*` 使用 `tests/fixtures/openwrt/` 中未修改的真实 functions/common/nand/fit/uci 脚本（来源及 SHA-256 见该目录 README），执行实际助手加载、查找 MTD/卷、重建 fit/rootfs_data、管道写入及回读；仅硬件命令仍为替身，不等价于 NAND、UBI 驱动或真实启动测试。

布局依据：`w1700k/installer-repo` commit `9a9684f398db7ffdbb39f685519e5535bf90352e` 的 `target/linux/airoha/dts/an7581-w1700k-ubi.dts`。vendor 为 `0/0x600000`、chainloader 为 `0x600000/0x100000`、ubi 为 `0x700000/0x1b700000`。检查的是正在运行的 Installer MTD 分区，不要求待修复 UBI 卷健康。

回读暂存文件最多为单个镜像大小，需要 initramfs 预留对应 RAM。目标 BusyBox 必须包含 `head -c`、`cmp -s`、`hexdump`；OpenWrt 默认配置具备这些 applet，但本轮未构建实际镜像验证。串口诊断 shell 阻止正常 preinit 收尾，故失败/取消时不承诺 SSH 可用。
