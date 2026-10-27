# 软件部署：从固定版本到机载控制台

本页负责安装与命令。第一次装机接着完成 [首次上机流程](docs/FIRST_RUN.md)，硬件接线见 [HARDWARE](HARDWARE.md)，打印装配见 [ASSEMBLY](ASSEMBLY.md)。默认路线是 D 短动作与颈部时序，不需要先训练模型；物理仿真是独立路线，见 [SIMULATION](SIMULATION.md)。

## 1. 软件运行在哪里

| 环节 | 设备 | 工作 | 依赖 |
|---|---|---|---|
| 离线预览 | Windows / Linux / macOS 电脑 | 参数、计划、DEMO，不接机器人 | Python、NumPy、pyserial |
| 实机执行 | RDK X5，Linux | IMU、15轴状态、D目标、颈部配合、日志和网页服务 | 同上，另需USB串口权限 |
| 操作界面 | 操作者电脑 | 经SSH转发访问X5，点击检查/复位/运行 | SSH客户端、浏览器 |
| 物理仿真 | 开发电脑 | MuJoCo模型加载、运行、分析 | 独立仿真依赖 |

D不依赖ROS、ONNX、CUDA或NPU。电脑不承担实时目标执行。两个串口分别属于微雪和JY901S，不能相互交换；SSH连通不等于舵机已使能。

## 2. 下载固定发布版

推荐 [v2026.10.27 Release](https://github.com/Xiaomiju-x/rdk-x5-microduck/releases/tag/v2026.10.27) 的完整资料包，解压后进入 `software/`。也可在电脑或X5自己的工作目录执行：

```sh
git clone --branch v2026.10.27 --depth 1 https://github.com/Xiaomiju-x/rdk-x5-microduck.git
cd rdk-x5-microduck/software
```

ZIP用户跳过clone。`main`用于后续开发；根目录早期Python文件、9月29日ZIP属于历史材料，当前入口为 `software/`。

## 3. 创建独立环境

语法最低Python 3.10。本版冻结组合为 **Windows x86_64 / CPython 3.12.14 / NumPy 2.2.6 / pyserial 3.5**，已做离线复测。仓库CI会在Windows/Linux、Python 3.10/3.12运行同一组离线测试，实际结果以对应提交Actions为准。公开包没有在本次发布中重新部署到X5；原型X5的精确系统镜像与Python版本尚未完整归档，不把电脑测试当作全ARM64环境认证。

Linux / X5：

```sh
python3 --version
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-tested.txt
```

如果系统缺少venv，按所装RDK系统的软件源安装对应 `python3-venv` 后重试。无需为D重装整板系统。RDK系统应选择与X5对应的官方镜像，并记录实际版本；[RDK官方文档](https://d-robotics.github.io/rdk_x_doc/)提供烧录、网络与系统配置说明。

Windows PowerShell：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-tested.txt
```

后续 `python` 均可替换为 `.\.venv\Scripts\python.exe`，不必修改脚本执行策略。希望试较新依赖时可用 `requirements.txt`，先测试再使用。报告环境时运行：

```sh
python -c "import platform,numpy,serial; print(platform.python_version(),platform.system(),platform.machine(),numpy.__version__,serial.__version__)"
```

## 4. 无硬件验证与页面预览

```sh
python -m unittest discover -s tests -v
python runtime.py plan --cycles 5
python app.py --demo --port 9194
```

测试应为 `OK`；plan关键字段如下（省略参数和SHA）：

```json
{"execute":false,"motion_writes":0,"cycles":5,"frames_per_cycle":400,"total_frames":2000,"all_cycle_endpoints_start":true}
```

浏览器打开 `http://127.0.0.1:9194/`，应显示 **DEMO · 无硬件**。运行只推进界面，不打开串口，也不是动力学仿真。体验后在启动它的终端按Ctrl+C；不要与实机页面共用端口。

本版34项离线回归：原24项加10项IMU诊断检查。1/2/3/5轮位置包仍与原等价证据SHA一致；D数据、成功参数与颈部算法未改。软件测试与实机展示是不同证据。

## 5. 准备X5与串口

1. 按官方文档安装系统、连网，确认可SSH登录。`your_user`、`your_x5_address`替换成自己的值。
2. 将仓库放到X5，或在X5执行第2节固定版本clone；进入software后创建环境。
3. 微雪USB-C数据口接X5 USB HOST，微雪选USB控制档，独立电源接动力输入。JY901S经另一USB-TTL接X5，接线见硬件页。
4. 保持只有一个串口控制器；本包不会替你停止旧步态或其他守护程序。
5. 列出串口：

```sh
python -m serial.tools.list_ports -v
ls -l /dev/serial/by-id/
```

先只插微雪数据线确认一条，再插IMU适配器确认另一条。优先记录稳定by-id路径；不要按上次ttyUSB0/1猜。插拔舵机三线接头前先断舵机动力电源。若权限不足，按系统管理员规定设置设备组访问，不对所有串口开放全局写权限。

## 6. 新舵机编号，已有机保留原标定

支持FT HD1910M、15轴ID1–15、1 Mbaud，以及项目已用固件的模式4。模式数字与固件有关，不是所有飞特型号的通用值；原型精确固件版本尚未完整归档，批次不同先核厂商表。

新购舵机可能有重复默认ID，应在装机前逐颗连接、设置并回读，再贴标签。可用厂商工具或固定版 [servo-web](https://github.com/fanhao375/microduck-replica/tree/f12827cd92272e91276246ac8958482e9bcb6c1f/tools/servo-web)。操作顺序见 [FIRST_RUN第2节](docs/FIRST_RUN.md#2-给新舵机编号已有机保留原标定)。

上游默认ID是 `20–24,30–34,10–14`，有独立的官方姿态与IMU200方案。本项目只参考其单颗扫描/寄存器工具；不导入上游全机站姿、一键校准或默认方向表。本包本身不写ID、模式、offset、P/D或EEPROM。

## 7. 创建自己的设备配置

第一次在software内创建：

```sh
python -c "from pathlib import Path; import shutil; Path('.local').mkdir(exist_ok=True); shutil.copyfile('config/robot.example.json','.local/robot.json')"
```

已有文件先备份，不重复覆盖。用文本编辑器填写：

| 字段 | 来源与填写时机 |
|---|---|
| `servo_port` / `imu_port` | 本机串口枚举；先填 |
| `servo_baud` / `imu_baud` | 1000000 / 115200，与实际设备核对 |
| `expected_mode` | 本项目为4，与固件表核对 |
| `start` | 正确站姿的本机读数，由capture填入 |
| `expected_offsets_raw` | 本机已有硬件offset原始字，由capture填入，不写回 |
| `directions_verified` | 逐轴ID、位置、增加计数方向确认后设true |
| `start_pose_verified` | 捕获的实物姿态与数值确认后设true |
| `body_from_sensor_rotation` | 传感器三轴在机体中的实际方向，见FIRST_RUN示例 |
| `imu_mount_verified` | 前后倾符号与实际一致后设true |

空模板与 `data/reference_pose_NOT_A_DEVICE_CONFIG.json` 不能发动作。D映射为“本机START+原历史增量”，要求FT结构、ID、物理方向及起始姿态一致；确认标志不会自动翻转关节方向。

## 8. 两个独立只读入口

舵机：

```sh
python runtime.py inspect --robot .local/robot.json
```

输出15轴id/mode/offset/torque/target/pos/voltage/temp/error，`motion_writes=0`。**inspect只检查舵机，不检查IMU。**

IMU：

```sh
python runtime.py imu-check --robot .local/robot.json --seconds 8
```

只开IMU口，不开舵机口，不发目标、不写传感器配置、不改验证标志。显示sensor欧拉角/角速度、body重力/角速度、前后倾变化、数据年龄及0x53/0x52主机接收频率。允许 `imu_mount_verified=false`，用于检查候选矩阵；验证方法见 [FIRST_RUN第5节](docs/FIRST_RUN.md#5-imu安装方向与只读验证)。

先结束占用同一IMU口的其他任务。工具读到数据不等于自动判断装对，也不会自动设置 `imu_mount_verified`。

## 9. 捕获START与慢复位

支撑机体，按首次上机站姿核对图摆正，保持不动：

```sh
python runtime.py capture --robot .local/robot.json --output .local/captured_robot.json
```

连续读三组位置；移动超过10counts则拒绝保存。只读保存实际位置和offset，`start_pose_verified`仍false。检查文件和实物后填写验证状态，把审核过的文件作为自己的 `.local/robot.json`；保留捕获前配置。

托稳躯干和头部、双脚卸重：

```sh
python runtime.py restore --robot .local/robot.json --supported
```

提示后留3秒，再将当前位置设目标、使能失能关节、慢回START。每拍最多6counts、约0.1秒；不改P/D、offset或EEPROM。个别关节偏离超过512counts（45°）或有故障，可先恢复其余：

```sh
python runtime.py restore --robot .local/robot.json --supported --partial
```

检查skipped，剩余关节单独处理。部分完成不等于可以放手。

## 10. 打开实机控制台

在X5的software及虚拟环境内：

```sh
python app.py --robot .local/robot.json --port 9194
```

电脑另开终端：

```sh
ssh -L 9194:127.0.0.1:9194 your_user@your_x5_address
```

电脑浏览器打开 `http://127.0.0.1:9194/`。确认不是DEMO；服务只监听X5 loopback。端口占用时两端一起换空闲端口，例如9197，不操作旧控制台。

首次顺序：只读检查→托稳复位→悬空单轮→平面自行站稳→有接护的落地单轮。参数含义与现场观察见FIRST_RUN。保存、切轮数、刷新不发动作；刷新默认单轮并清空现场确认。

命令行等价入口：

```sh
python runtime.py run --robot .local/robot.json --parameters config/success_20261023.json --cycles 1 --onsite-ready
```

首150帧准备后进入动作。多轮可将cycles改2、3、5，每轮完整准备、动作、回位、保持。实拍来自原型原运行版本；公开包是离线核验，多轮稳定性仍需实物验证，见 [RELEASE](RELEASE.md)。

## 11. 常见问题与日志

| 现象 | 检查与处理 |
|---|---|
| 页面是DEMO | 检查启动参数是否含robot、是否打开旧端口 |
| 串口打不开 | list_ports、权限、其他程序占用 |
| 15只均不回复 | 微雪动力电源/USB档/总线插头，先恢复只读通信 |
| 部分ID缺失或重复 | 编号标签、单颗扫描、分支接线 |
| IMU无数据 | 独立串口、115200、0x52/0x53输出；厂商工具设置后只读重查 |
| IMU前后反向 | 模块轴标识、rotation的三列、固定状态 |
| 模式/offset/坐标不符 | 查实际与配置的差异，不套别台START |
| 程序结束但未站稳 | 看现场视频、起步/走动/收步、载荷与脚底接触 |

“停止发目标”或Ctrl+C只停止后续目标，不自动卸力、猛回START或重试。先支撑，再显式读取和复位。记录在 `.local/records/`，任务摘要 `.local/jobs/`，参数 `.local/preset.json`；公开前去除凭据、串口序列号和私人路径，见 [CONTRIBUTING](CONTRIBUTING.md)。

本版增加诊断与教程，D400帧、颈部算法、成功默认、协议和动作路径保持。原1/2/3/5轮假反馈位置包SHA回归通过；IMU诊断覆盖频率、符号、旋转、无舵机访问、错误清理与取消。没有因本次发布连接机器人或操作舵机。
