# 飞特总线实现来源与兼容改动

来源：fanhao375/microduck-replica，`tools/servo-web/feetech.py`。

https://github.com/fanhao375/microduck-replica/blob/master/tools/servo-web/feetech.py

本项目最初复制的上游文件 SHA-256：

`6523fcf728393f9f185edbc6760a538474b8a009e298f2444849b0c4558dad9a`

原声明与 Apache-2.0 许可保留于 [LICENSE](LICENSE)。`software/data/provenance.json` 中的 `upstream_bus_sha256` 表示这个原始来源文件，而非带以下兼容改动后的文件。

## v2026.10.27.1 兼容修正

GitHub Actions 在 Windows 和 Ubuntu 的 Python 3.10 上发现，原 `_read_status` 的调试 f-string 在表达式内包含 `b'\xff\xff'`，该语法需要 Python 3.12。现将同一 `hexs(...)` 表达式先赋给 `packet_text`，再插入 f-string。

只改变调试字符串的写法。帧头、包格式、校验、收发、状态解码、返回值与动作指令均保持。离线检查确认原版与修正版对同一应答产生完全相同的返回值和 trace 文本；软件源码通过 Python 3.10 语法解析检查，并重跑完整 34 项回归。实际跨版本 CI 结果以对应提交的 Actions 为准。

本次没有连接舵机或重新测试实机。
