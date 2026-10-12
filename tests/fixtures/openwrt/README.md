# Pinned OpenWrt helper fixtures

Unmodified upstream files from `w1700k/installer-repo` commit
`9a9684f398db7ffdbb39f685519e5535bf90352e`.

Base URL: https://raw.githubusercontent.com/w1700k/installer-repo/9a9684f398db7ffdbb39f685519e5535bf90352e/

| Fixture | Upstream path | SHA-256 |
|---|---|---|
| functions.sh | package/base-files/files/lib/functions.sh | e819c5a6ccc2737233a2e4497745518d55fcde48511fa324a2bed40c7a59db24 |
| common.sh | package/base-files/files/lib/upgrade/common.sh | c33b304881f13b55684e41d852835f885798fe752a1c075c6b9588b6174af16d |
| nand.sh | package/base-files/files/lib/upgrade/nand.sh | 383c40461e2753af8f00f5cf16177330f05842fa6e1c5c2b1e02593450defd78 |
| fit.sh | package/utils/fitblk/files/fit.sh | fe76027ce9266c2d195cddae9767baea6cff02c4c55fc5f73a71bded29ef55e7 |
| uci.sh | package/system/uci/files/lib/config/uci.sh | 08b91a09a010137cf2a5fea5b75cf6898bdc7358405769b6c7432a98aeb2c7a4 |

These fixtures execute only inside disposable test chroots. Hardware commands
remain stubs; no host device nodes or filesystems are mounted. Keep upstream
copyright notices. Do not replace helper functions with empty stubs in the
real-helper integration scenarios.
