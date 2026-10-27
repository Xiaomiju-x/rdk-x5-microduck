# 仿真环境与算法研究：从离线模型到后续 RL

本章给出一个随发布包提供、可以直接在电脑运行的 **FT 几何教学仿真**，并说明它与当前实机方案、上游训练工程之间的关系。完成本章不需要机器人上电，也不需要先有 RTX 5090。

如果你的目标是复刻本次短距离前进，主路径仍是 [硬件](HARDWARE.md) → [装配](ASSEMBLY.md) → [设备配置](DEPLOYMENT.md) → `software/` 中的 D 控制台。仿真是学习坐标、关节、载荷、接触和后续算法研究的独立入口。

## 1. 先区分三种运行环境

| 环境 | 在哪里运行 | 输入与输出 | 本版本提供什么 |
|---|---|---|---|
| D 控制台 DEMO | 普通电脑 | 参数、轮数 → 页面进度与模拟任务记录 | `software/app.py --demo`，不计算机器人动力学 |
| FT 教学仿真 | 普通电脑CPU，图形预览需要OpenGL | MJCF几何/物理参数、目标角 → MuJoCo状态、接触、统计、可视化 | 本章 `simulation/` 的自包含模型与可执行例子 |
| RL训练及部署研究 | 通常Linux + CUDA GPU；板端推理另行适配 | 模型、观测、动作定义、奖励 → 权重 → 离线验证 → 实机接管 | 固定上游参考及适配步骤；本发布包不附已验收的FT行走权重 |

当前成功实拍使用 D 短目标片段和分段颈部时序。成功预设的自动前/后倾增益均为0，不能因为程序读取IMU，就把它写成全身实时RL平衡。教学模型也没有重放这段实机动作来证明行走效果。

## 2. 目录里具体有什么

```text
simulation/
├── run.py                    # inspect / hold / joint 三个离线入口
├── requirements.txt          # 本轮实测的直接依赖版本
├── test_simulation.py        # 4项无显示器、无硬件模型检查
├── model/
│   ├── ft_bare.xml           # FT裸机参考MJCF、地面、灯光、14个执行器
│   ├── meshes/              # 15份分组凸包STL，随包提供
│   └── manifest.json        # 来源、假设、关节顺序和全部模型文件哈希
├── payload_example.json     # 假设84g方块的教学例子，非成功样机配置
├── verification/            # 发布时实际执行所得JSON
└── media/                   # 真实MuJoCo渲染截图与2秒教学视频
```

程序加载前验证模型文件哈希，避免演示过程中误用其他版本。本章命令使用发布包中的基准文件。初次研究载荷时只复制/修改 `payload_example.json`，通过 `--payload` 传入，不需要修改基准MJCF或manifest。

若要改关节、接触或执行器，应先复制整个 `simulation/` 为自己的研究目录，保留原manifest；修改后记录变更理由与来源，并用下面的命令在**研究副本目录**更新该副本的文件哈希。新结果将属于你的新模型，不能继续标成发布基准通过：

```sh
python -c "from pathlib import Path; import json,hashlib; p=Path('model/manifest.json'); raw=p.read_bytes(); m=json.loads(raw); m['research_parent_manifest_sha256']=hashlib.sha256(raw).hexdigest(); m['purpose']='USER RESEARCH COPY - document physical changes before interpreting results'; m['files_sha256']={k:hashlib.sha256((p.parent/k).read_bytes()).hexdigest() for k in m['files_sha256']}; p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf8')"
```

此命令只重新登记副本内容，不检查你改出的物理参数是否正确。必须同时保存自己的改动说明，不能把重新计算哈希当成模型验证。

## 3. 模型来源、坐标和简化

几何依据为机械行者Robo / fanhao375的飞特复刻CAD，固定来源说明：
https://github.com/fanhao375/microduck-replica-cad/tree/22ecf4daea158f2dfad7b633f730a5c04f1e04e0

本项目按刚体将FT CAD显示网格分组、转换为凸包，再建立MuJoCo关节树；不是把官方XL330模型改一个名字。公开模型与几何渲染按 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) 保留上游署名，Python示例按Apache-2.0开放。详见 [simulation/NOTICE.md](simulation/NOTICE.md)。

| 项目 | 本目录采用的定义 |
|---|---|
| 世界/机体方向 | 参考姿态下，+X朝嘴巴，+Y朝鸭子左侧，+Z向上 |
| 长度、质量、角度 | 米、千克、弧度；命令报告中的角度另转成度 |
| 关节 | 15个转动关节：两腿10、头颈4、嘴1；自由站立另有一个free root |
| 主动输出 | 14个位置执行器；嘴作为被动关节，不插入策略动作向量 |
| 主动顺序 | 左腿1–5 → 头颈11–14 → 右腿6–10，不能假定是ID1–14顺序 |
| 物理步长 | 0.005秒，即200Hz；与真实串口循环频率不是同一项 |
| 裸机总质量 | 0.611kg，采用历史本体称重作基线；各连杆质量比例及箱体惯量为估计 |
| 参考姿态 | 项目求解过的近似CAD双脚姿态；不等于实机编码器START或精密零位 |
| 执行器 | 理想位置PD，kp=4.8126293、kv=0.1407062、力矩限值±0.9226667N·m |
| 地面接触 | 脚部凸包与地面、双脚之间；完整躯干/头部自碰撞没有建模 |
| 当前没有 | 电池、X5、微雪、安装架和额外配重；电压下降、发热、齿隙、胶粘滑移与TPU形变 |

这里的kp/kv不是舵机寄存器P32/D40。0.611kg也不是10月23日整机重量。本次主动移除了早期胸前/后低位载荷估计，避免将旧布局当作成功当天的数字模型。想研究真实机载平衡，需要先补齐实物装载和执行器参数。

![MuJoCo中的FT裸机教学模型](simulation/media/ft-reference.png)

这是简化的凸包物理参考外形，用来观察关节和接触；打印和孔位设计仍使用 [mechanical/](mechanical/)，不要从这些凸包STL重新打印机体。

## 4. 第一步：准备独立的电脑环境

本轮实测环境：Windows、Python 3.12.14、MuJoCo 3.10.0、NumPy 2.3.5、Pillow 12.3.0。其他系统可按MuJoCo官方安装说明配置，但不能将本轮Windows检查写成已覆盖所有系统。

建议为仿真单独建虚拟环境，避免与X5运行程序或CUDA训练环境混在一起。以下从仓库根目录开始。

**Windows PowerShell：**

```powershell
cd simulation
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest -v test_simulation
```

如果未安装Windows `py` 启动器，可用指向Python3.12的 `python` 替代创建环境那一行。后续示例统一写 `python`；Windows可全部替换成 `.\.venv\Scripts\python.exe`。

**Linux：**

```sh
cd simulation
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest -v test_simulation
```

Mac的无窗口检查按普通Python环境运行；交互窗口使用MuJoCo随包提供的 `mjpython` 启动器，例如 `mjpython run.py joint --viewer`。图形系统说明见：
https://mujoco.readthedocs.io/en/stable/python.html

**完成标志：** 4项测试通过。这里只检查模型能编译、质量/关节维度一致、悬空模型只移除基座自由度、附加质量生效及短关节例子能完成；没有访问真实设备。

## 5. 第二步：只读查看模型

```sh
python run.py inspect --output .local/inspect.json
```

主要输出应为：

```json
{
  "mode": "inspect",
  "hardware_io": false,
  "total_mass_kg": 0.611,
  "joint_count": 15,
  "actuator_count": 14,
  "timestep_s": 0.005,
  "steps": 0
}
```

`initial_com_world_m` 是这个假设模型的质心，不是照片中实机的测量质心。输出还包含MuJoCo/Python版本及模型哈希，便于对照双方使用的是不是同一模型。

## 6. 第三步：运行自由基座的短保持

```sh
python run.py hold --seconds 2 --output .local/hold.json
```

程序保留自由基座和重力，14个执行器保持模型参考角，让MuJoCo积分2秒。它不会锁住根部位置，也不会人为把根部轨迹往前移动。

本次执行完成400个物理步，数值状态有限、MuJoCo警告计数为0；此模型最大倾斜约2.50°，峰值接触数6。实际记录见 [hold.json](simulation/verification/hold.json)。不同环境数值结果允许有微小差异，不能把2秒静态保持当成动态步态通过。

可选查看图形窗口：

```sh
python run.py hold --seconds 8 --viewer
```

窗口关闭会结束本次演示。8秒是你主动运行的新观察，不属于前述已记录的2秒发布验证。

## 7. 第四步：看清双膝小幅响应

```sh
python run.py joint --seconds 2 --output .local/joint.json
```

该模式**将躯干固定在空中**，给双膝施加方向相反、平滑起落的小幅目标，其他执行器保持参考角。目的是检查模型关节响应和程序链路，不是演示落地前进。正弦乘平滑包络，目标绝对偏移小于5°，不是每只膝盖一定达到±5°。

本次记录：400步、2秒、无MuJoCo警告；两膝实际全摆幅约6.48°。头颈和其他轴因重力/耦合有微小跟随误差，躯干固定所产生的约束不代表真实机器人能自己平衡。[joint.json](simulation/verification/joint.json)

```sh
python run.py joint --seconds 2 --viewer
python run.py joint --seconds 2 --image .local/preview.png
```

[观看发布时生成的2秒关节教学视频](simulation/media/ft-joint-teaching.mp4)

导出MP4需要另外安装FFmpeg并放到PATH。静态检查和JSON统计不需要它：

```sh
python run.py joint --seconds 2 --video .local/joint.mp4
```

也可用 `--ffmpeg` 传入自己机器上的可执行文件路径。视频自带“SIMULATION ONLY / not walking validation”标记；不得把它与成功实机视频拼接后误写成连续行走证据。

## 8. 第五步：理解载荷如何进入模型

本包提供一个明确标成假设的84g方块例子，放在躯干坐标x=0.06m处：

```sh
python run.py inspect --payload payload_example.json --output .local/with_payload.json
python run.py hold --seconds 2 --payload payload_example.json --output .local/payload_hold.json
```

模型总质量应从0.611变成0.695kg，初始质心也会变化。方块以实心长方体惯量近似，配置的 `full_size_m` 是完整长宽高，程序内部再换成MuJoCo半尺寸。附加载荷固定在躯干上，仅参与惯量/重力，不启用其碰撞。

发布时实际跑这份假设载荷的2秒保持，模型发生翻倒。由于本模型只启用脚部接触，翻倒后躯干/头部可能穿过地面，那一阶段不能用于分析真实碰撞或损坏。`complete=true`仅表示积分步数完成，不表示站立或行走通过。这个例子展示的是“载荷会改变结果”，不是成功样机配重方案。

研究自己的安装方式时，复制该JSON，逐项填写**自己测量的**质量、相对躯干参考原点的三维中心、外形尺寸，再保存为新文件。每次只比较一个变化，固定动作、接触、PD、模型姿态和随机种子。不要用未知质量的填充物或不明胶点位置推导“足够稳定”的精确结论。

10月23日成功配置有两侧电池、背侧X5和前下方附加件；该配置的完整质量/中心尚未测齐。因此本包不提供一份声称与成功样机完全等价的载荷JSON，也不把本例的0.695kg写成鸭子当前重量。

## 9. 后续接入RL时，哪些东西必须对齐

从本章走向RL需要额外建立训练任务，而不是给 `run.py` 加一个网络推理就完成。建议按以下工件推进：

| 阶段 | 输入 | 应交付的可检查结果 |
|---|---|---|
| 几何与姿态 | 选定FT CAD、逐轴方向、参考站姿 | 关节轴、顺序、零点定义及正反向映射表 |
| 质量与接触 | 本机连杆/附件质量、位置、脚垫和地面 | 质量表、惯量估计方法、接触参数与不确定范围 |
| 执行器辨识 | 相同目标在悬空/带载下的反馈、供电条件 | 扭矩/速度/延迟/摩擦等模型依据；不将寄存器D值直接当物理阻尼 |
| 训练接口 | 观测向量、单位、滤波、历史、动作尺度 | 训练与推理一致的接口定义和同输入对照 |
| 仿真评估 | 固定版本模型、权重、起停命令 | 起步、前进、收步、扰动、延迟和载荷变化的记录 |
| 实机适配 | 已确认的逐机START、IMU方向和执行链路 | 独立的受控接管与试走记录，再决定是否切换默认动作 |

本章14维输出的顺序是模型定义；软件D控制器以15个舵机ID发目标。两者不能只按数组长度截取、交换或补0。执行器输出、模型q角、舵机raw计数和硬件offset是四个不同概念。

### 固定上游研究入口

Pollen Robotics的Microduck RL工程采用mjlab / MuJoCo Warp和PPO，参考版本：
https://github.com/pollen-robotics/microduck_rl/tree/273afe0b31c4ab365b9ff806a927b63ac92b5ddd

该版本的 `pyproject.toml` 声明Python3.12、mjlab1.3.0、warp-lang1.12.0、PyTorch2.9.1等依赖，并维护 `uv.lock`。其原生执行器路线是Dynamixel XL330及BAM模型，不是本机HD1910M。上游训练说明、任务注册、导出和CPU部署演练应按**这个固定版本**阅读，不把网上其他版本的命令混用。

如仅获取研究源码：

```sh
git clone https://github.com/pollen-robotics/microduck_rl.git
cd microduck_rl
git checkout 273afe0b31c4ab365b9ff806a927b63ac92b5ddd
```

研究环境单独建，按该版本README配置CUDA与uv；训练入口、环境名、导出方法直接取自其固定文档。**本轮没有重新安装或运行这个GPU训练环境**，不把上述取源码步骤写成已通过的FT训练流程，也没有用新权重改变成功D动作。

RTX5090等CUDA计算资源可用于后续并行训练，但本章CPU仿真和当前D机载执行均不依赖它。选择训练服务器不能替代FT几何、质量分布、执行器、动作映射和观测接口适配。

## 10. 常见问题

| 现象 | 先检查 |
|---|---|
| 看到DEMO进度，但没有3D机器人 | DEMO是网页流程演示；3D入口为本章 `run.py ... --viewer` |
| `ModuleNotFoundError: mujoco` | 是否在simulation虚拟环境安装依赖；是否误用了software虚拟环境的解释器 |
| 模型资源hash不符 | 是否修改/覆盖了模型文件；从固定Release重新取基准，在副本中做研究 |
| JSON能跑，窗口或PNG报OpenGL错误 | 物理计算不需要显示器；图形模式需要有效OpenGL环境。先完成无窗口命令，再按MuJoCo官方说明配置EGL/OSMesa或桌面驱动 |
| Mac的被动窗口启动失败 | 使用 `mjpython` 替代 `python`；无窗口计算仍可普通Python运行 |
| 模型跌倒或加质量后更不稳 | 这是所选模型/控制假设的结果，不代表实机已被验证不行，也不要锁住根部后再称自由站立 |
| 想直接把qpos写到舵机 | 本模型没有实机校准合同；去设备配置流程核对映射，不能直接发送仿真角度 |
| 想用陆吾的权重 | 几何、零点、执行器和训练接口不同，不能以外形相似认定可直接复用 |

## 11. 本次验证能说明什么

本次实际完成模型加载、400步自由基座保持、400步悬空双膝教学响应、PNG/MP4渲染和4项测试。CPU物理计算、输出文件及图像均可由本包重做，结果见 [verification/](simulation/verification/)。

它证明本目录提供了可运行的建模与仿真起点；不证明D轨迹在该模型中稳定、不证明成功样机的载荷分布已还原，也不证明完整RL或长距离行走已完成。实机成果继续以 [成功视频与参数](progress/2026-10-23/README.md) 为依据。
