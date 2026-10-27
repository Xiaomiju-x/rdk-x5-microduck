# 当前文档更新｜24章手册与单电池启动（2026-10-27）

`main`已与地瓜社区同步[六篇24章完整手册](docs/FULL_SOLUTION.md)，新增[单电池供电启动记录](progress/2026-10-27/README.md)、[R9接线与结构说明](docs/SINGLE_POWER_R9.md)及一致的[后续路线](ROADMAP.md)。最新现场确认：一块现有5V电池经微雪DC+/DC−分供后，X5和15个舵机可以正常供电、启动。带载行走、连续运行和R9实配仍待验证。

本次为文档、进度和图示同步，不改控制软件、成功D参数、模型或已发布机械文件。固定运行/打印版本仍为 **v2026.10.27.1**；旧tag和下载ZIP保持原样，不将新R9说成已进入旧包。下面保留该固定版说明，其“15章”是当时发布状态，最新在线教程已为24章。

---

## v2026.10.27.1 · 固定版原发布说明

本版在10月26日固定开源包基础上，将资料重组为从采购到装配、软件、仿真与首次实机的完整案例。原型成果仍以10月23日全机载短距离实拍为依据，本次没有新增实机行走、标定或控制参数修改。

## 新增与改进

- 15章完整案例；独立采购、选件、配置卡、首次上机教程和操作检查表。
- 全新系统框架、复刻流程、成功原型配置卡、机体坐标图，提供SVG/PNG。
- 28个选定FT本体STL，逐件来源校验；与R8A六实体及两TPU脚底配套。52对象取舍CSV完整记录保留、替代、可选与排除项。
- 公开软件新增独立只读 `imu-check`，补传感器安装矩阵与输出解释；D目标序列、颈部算法和成功参数保持。
- 自包含MuJoCo FT教学模型、15份网格、CPU检查/保持/双膝实验、实际渲染图与教学视频。
- 固定下载入口、已测依赖、Windows/Linux CI、3类Issue模板与贡献指南。
- 明确下一阶段：一块电池、减少线缆裸露、长距离行走、RL实时闭环；V2机内集成并行推进。

## 推荐入口

[完整案例](docs/FULL_SOLUTION.md) → [采购](docs/PROCUREMENT.md) → [装配](ASSEMBLY.md) → [首次运行](docs/FIRST_RUN.md)。

无硬件读者可从 [DEMO](DEPLOYMENT.md) 和 [仿真环境](SIMULATION.md)开始。

固定Release：https://github.com/Xiaomiju-x/rdk-x5-microduck/releases/tag/v2026.10.27.1

## Python 3.10兼容修订

首次远端CI发现上游串口模块的调试f-string写法需要Python3.12。修订版只调整字符串兼容写法，保留数据包与动作算法，重新验证3.10/3.12。初始v2026.10.27源码标签保留，推荐以本修订版为准。

## 本版实际验证

| 项目 | 结果 | 证据 |
|---|---|---|
| 公开控制软件 | 34项离线测试通过，包括原24项和新增IMU只读诊断测试 | `software/verification/offline_20261027.json` |
| D动作保持 | 9个关键函数AST与前版一致；轨迹、neck、成功配置等文件逐字节不变；1/2/3/5轮位置包回归通过 | 同上；历史等价证据保留在`software/data/offline_equivalence.json` |
| 仿真独立环境 | Windows/Python3.12.14、MuJoCo3.10.0、NumPy2.3.5、Pillow12.3.0；4项测试通过 | `simulation/verification/clean_environment.json` |
| 自由基座保持 | 模型2秒400步、无数值警告；模型最大倾角约2.50° | `simulation/verification/hold.json` |
| 固定躯干双膝实验 | 2秒400步、实际全摆幅约6.48°、无数值警告，PNG/MP4已渲染 | `simulation/verification/joint.json` |
| 机械文件 | 28个本体STL与冻结来源哈希一致；沿用R8A与TPU已公开几何 | `mechanical/body_parts/manifest.json` / `mechanical/manifest.json` |
| 文档与发布包 | 相对链接、打包内容及逐文件SHA检查 | 根`SHA256SUMS.json`，Release附件SHA见Release页面 |

CI文件已提供，远端具体运行状态请看仓库Actions，不能以本地测试替代未发生的远端结果。

## 验证范围

实机成功的是10月23日原型及其保存参数。公开包离线等价、仿真教学和新复刻机实测分别记录。连续2/3/5轮、长距离及全身RL闭环仍待相应实机验证。模型为裸机教学参考，未把两侧电池和前部附加件的未知参数编成精确数字孪生。

默认仍为：启动0°、走动请求−30°、保持0秒、过渡0.2秒、提前收颈1.1秒、自动双向增益0。设备START、offset和IMU矩阵均按自己机器填写。

## 历史与许可

[v2026.10.26发布说明](history/RELEASE_20261026.md)与原固定Release保留；不覆盖旧tag或旧附件。根目录早期模块与9月ZIP仅供历史研究。软件、FT衍生结构、渲染和实拍按[NOTICE](NOTICE.md)分类许可使用。
