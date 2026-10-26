# 软件部署与逐机配置

本次推荐入口为 [software/](software/README.md) 的 **D 短距离前进公开运行包**。根目录早期源码与 `microduck-source-20260929.zip` 保留为研发历史，不是最新安装入口。

D 目标和颈部算法来自已经演示的全机载原型；公开版将设备配置外置，直接运行在 X5，电脑浏览器通过 SSH 隧道访问。公开移植包已做离线对照，未在此次发布中重新执行实机动作。新机需要自己的编号、方向和站姿校验。

## 1. 环境与无硬件预览

Python 3.10+，X5 使用 Linux；笔记本可用 Windows/Linux/macOS 运行计划和 DEMO。依赖为 NumPy、pyserial，D 不需要 ONNX、ROS、CUDA 或训练服务器。

```sh
git clone https://github.com/Xiaomiju-x/rdk-x5-microduck.git
cd rdk-x5-microduck/software
python -m venv .venv
```

Linux/macOS 激活：

```sh
. .venv/bin/activate
```

Windows PowerShell 可直接使用 `.venv\Scripts\python.exe` 替换下文 `python`。Linux 若只有 `python3`，先用 `python3 -m venv .venv` 创建环境。

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python runtime.py plan --cycles 5
python app.py --demo --port 9194
```

打开 <http://127.0.0.1:9194/>，应显示 **DEMO · 无硬件**。点击运行仅演示进度。`plan` 输出 2000 帧、`execute=false`、`motion_writes=0`。无需连接机器人即可完成以上步骤。

## 2. 确认本机硬件合同

本包沿用项目 FT 结构的 HD1910M 舵机，固定 ID 1～15、舵机 1 Mbaud、JY901S 115200 baud、舵机模式 4（本项目固件的位置模式）。不同舵机、固件、机械版本不能直接套用。

按 [HARDWARE.md](HARDWARE.md) 核对实际编号和方向；11 号是颈根，**raw 增加后移、raw 减少前移**。外形类似不代表可复制陆吾机型零位、方向或步态。

本程序不写 ID、工作模式、offset、P/D 或 EEPROM。首次编号和模式设置可使用 [上游 servo-web 工具及文档](https://github.com/fanhao375/microduck-replica/tree/master/tools/servo-web)。按其流程在卸重状态逐轴确认，再进入本包。不要同时启动两个串口控制器。

## 3. 本机配置

在 `software` 内创建本地配置：

```sh
python -c "from pathlib import Path; import shutil; Path('.local').mkdir(exist_ok=True); shutil.copyfile('config/robot.example.json','.local/robot.json')"
```

编辑 `.local/robot.json`：

|字段|填写要求|
|---|---|
|`servo_port`|微雪实际串口；Linux 优先使用本机 `/dev/serial/by-id/...` 稳定路径|
|`imu_port`|IMU USB-TTL 串口，与舵机串口不同|
|`servo_baud` / `imu_baud`|1000000 / 115200；程序不修改设备波特率|
|`start`|本机正确初始站姿的实际读数，ID 1～15 全部需要|
|`expected_offsets_raw`|本机读出的硬件 offset，不是待写标定值|
|`expected_mode`|本项目对应 4；不匹配拒绝动作，不自动改模式|
|`directions_verified`|实际 ID、方向、结构版本核对后才设 `true`|
|`start_pose_verified`|确认捕获的是正确站姿后才设 `true`|
|`body_from_sensor_rotation`|固定传感器到机体旋转矩阵；机体 x 向前、y 向左、z 向上|
|`imu_mount_verified`|核对安装方向、前后倾符号后才设 `true`|

空模板和 `data/reference_pose_NOT_A_DEVICE_CONFIG.json` 均不能直接发动作。后者仅是历史原型参考，供离线比对。

用 `python -m serial.tools.list_ports -v` 查看串口，并确认当前用户有访问权限。两个 USB 串口的编号可能变化，不能仅按上次 ttyUSB0/1 猜测。

先只读：

```sh
python runtime.py inspect --robot .local/robot.json
```

不会使能或发目标。编号缺失、模式错误、坐标异常时，先核实接线、设备模式与实物状态。

## 4. 只读捕获 START，原标定不变

参照装配站姿和正侧图，在机体稳定支撑时摆好自己的初始姿态。已有正确站姿可直接捕获，不需要将 15 轴全失能重摆。

```sh
python runtime.py capture --robot .local/robot.json --output .local/captured_robot.json
```

该命令连续读三次位置，拒绝明显移动的姿态；保存实际位置和 offset，不使能、不改舵机寄存器。输出的 `start_pose_verified` 仍为 `false`。先核实实物姿态和数值，再设为 `true`，用该文件替换自己的运行配置。

捕获只定义参考姿态，不等于动态验证。映射是各轴 `本机 START + 历史增量`，要求结构、ID、物理方向及起始姿态相符。

## 5. IMU 与反馈

JY901S 应输出欧拉角 0x53 和角速度 0x52，本项目约 50 Hz。`imu.py` 只读，不写配置；输出格式或波特率不同时先按厂商工具文档设置。

若传感器轴与机体 x 向前、y 向左、z 向上完全对齐，可填单位矩阵；否则根据固定安装方向填写 `body_from_sensor_rotation`，要求正交、行列式 +1。历史原型的候选安装角不等于另一台机器的实测安装角。

程序把传感器欧拉角转换为重力方向，再乘固定矩阵；相对初始姿态的 pitch 增加代表前倾。先支撑机体核对前后倾符号，再启用自动反馈。成功预设 `gain/back_gain` 都是 0，采用定角及提前收颈，但仍要求 IMU 新鲜数据。

## 6. 托稳慢复位

配置核对后，托稳躯干与头部，双脚完全卸重：

```sh
python runtime.py restore --robot .local/robot.json --supported
```

程序通知并等待 3 秒，读取所有关节。每个关节先将目标设为刚读到的实际位置，回读确认，再使能原先失能的关节；之后每拍不超过 6 counts，约 0.1 秒一拍慢回本机 START。偏离超过 512 counts（45°）或有故障的关节不会盲目大幅复位。

可先恢复其余正常关节：

```sh
python runtime.py restore --robot .local/robot.json --supported --partial
```

日志会列出 skipped。仍需托稳，部分完成不代表整机复位。只写易失目标和必要的使能状态，不修改 P/D、offset、模式或 EEPROM。

## 7. 控制台调试

X5 上：

```sh
python app.py --robot .local/robot.json --port 9194
```

电脑另一终端：

```sh
ssh -L 9194:127.0.0.1:9194 your_user@your_x5_address
```

打开 <http://127.0.0.1:9194/>。端口占用时，两端一起改成同一个新端口；不要同时运行旧硬件控制台。服务仅监听 X5 loopback，没有公网运动控制入口。

默认使用成功单轮参数，轮数与颈部参数独立。新机先托稳悬空确认运动方向和净空，再在平整防滑面进行有接护的单轮观察。每次动作前重新勾选对应现场状态。切换、保存、刷新不发动作。

命令行等价入口，仅在现场准备好时执行：

```sh
python runtime.py run --robot .local/robot.json --parameters config/success_20261023.json --cycles 1 --onsite-ready
```

首 150 帧保持准备，之后动作。多轮可将 `--cycles` 改 2、3、5，每轮含完整准备、动作、回位、保持；它是延长短动作的实验入口，不是长距离稳定行走已验证的声明。

## 8. 停止、记录与验证

控制台“停止发目标”或命令行 Ctrl+C 停止后续目标，不自动卸力、回 START 或再试下一轮。通信、真实故障状态、失能、坐标/模式/offset 改变、IMU 停更仍检查；低电压与普通跟随误差按原实验设置记录，不改舵机自身保护。

逐帧记录位于 `software/.local/records/`，任务摘要 `.local/jobs/`，保存参数 `.local/preset.json`。包含轮次、目标、实际反馈与颈部状态；默认不提交公共仓库。

400 帧腿部增量、时间间隔、颈部算法和成功参数保持。公开运行器与原运行器的 1/2/3/5 轮假串口位置包逐字节一致，见 [离线等价证据](software/data/offline_equivalence.json)。测试另覆盖停止/故障不续跑、只读捕获、使能顺序、配置拒绝和界面互斥。软件检查不替代新机悬空/落地验证，也不把回 START 当作物理站稳。

RL 闭环、长距离和 V2 机内集成按 [ROADMAP.md](ROADMAP.md) 推进，不作为本次资料发布前置条件。
