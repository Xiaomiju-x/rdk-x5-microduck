# RDK X5 Duck｜完整开源参考方案

**从打印装配、机载集成到短距离前进，把机器鸭的结构、硬件、控制软件和调试经验一起开放。**

RDK X5、微雪 Bus Servo Adapter (A) 和电池全部安装到鸭子本体后，我们已实现平整地面上的短距离前进，并在这次展示结束时保持站立。这个仓库面向希望复刻、教学或继续研究双足机器人的开发者，提供一条围绕现有 RDK X5 开发板展开的完整参考路径。

**方案发布：2026-10-26 · 实机成果：2026-10-23**

[完整方案文章](docs/FULL_SOLUTION.md) · [地瓜社区主帖](https://forum.d-robotics.cc/t/topic/35728) · [下载仓库ZIP](https://github.com/Xiaomiju-x/rdk-x5-microduck/archive/refs/heads/main.zip) · [版本与验证说明](RELEASE.md)

## 先看实际效果

[▶ 全机载短距离前进与硬件展示（完整实拍）](media/20261023/onboard-short-walk.mp4)

| 正面：驱动与供电 | 侧面：贴身安装布局 |
|---|---|
| ![正面](media/20261023/onboard-front.jpg) | ![侧面](media/20261023/onboard-side.jpg) |

完整视频约13秒，前段为短距离前进，后段展示机载硬件。当前成果来自本台原型的D短动作及颈根时序微调；长距离、不同地面和全身实时RL行走继续独立验证。

## 本次开放什么

| 资料 | 入口 | 用途 |
|---|---|---|
| 完整方案与复现顺序 | [FULL_SOLUTION](docs/FULL_SOLUTION.md) | 从成果到搭建、部署、调试的一篇总览 |
| 最新硬件选型、接口与接线 | [HARDWARE](HARDWARE.md) | X5、微雪、15轴舵机、IMU和两路供电 |
| 本体来源、轻量安装件与脚垫 | [ASSEMBLY](ASSEMBLY.md) / [机械文件](mechanical/) | 上游FT本体入口、本项目改件的可编辑模型和打印说明 |
| 成功D动作的公开运行包 | [software](software/) | 控制台、相对目标序列、颈部时序、串口/IMU与逐机配置 |
| 安装与首次上机 | [DEPLOYMENT](DEPLOYMENT.md) | 依赖、离线检查、各机START建立、只读检查与托稳复位 |
| 成功参数与媒体 | [2026-10-23](progress/2026-10-23/README.md) | 原型演示的参数与事实依据 |
| 装配和调试经验 | [PITFALLS](PITFALLS.md) / [BUILD_LOG](BUILD_LOG.md) | 失败案例与迭代过程 |
| 来源、许可与贡献 | [NOTICE](NOTICE.md) / [CONTRIBUTIONS](CONTRIBUTIONS.md) | 区分本项目工作和上游设计 |

## 快速开始：先运行离线控制台

安装Python 3.10或更新版本，下载或克隆本仓库，在仓库目录执行：

```sh
cd software
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python runtime.py plan --cycles 5
python app.py --demo --port 9194
```

打开 `http://127.0.0.1:9194/`。DEMO不访问串口；运行按钮演示流程，不能据此判断物理行走效果。连接真实X5前，请完成[部署与逐机配置](DEPLOYMENT.md)。新机需要确认编号、方向、模式、offset和自己的START，不能把原型坐标当通用零位。

## 当前默认动作

D使用记录的短距离目标片段，配合**11号颈根的启动角、走动角和平滑提前回位**。腿部目标和节奏保留为基准，颈部参数独立可调。

| 参数 | 10月23日成功配置 |
|---|---:|
| 启动角，相对本机START | 0° |
| 走动角，请求值 | 前移30°（代码−30） |
| 起步保持 / 角度过渡 | 0秒 / 0.2秒 |
| 提前收颈 | 1.1秒 |
| 自动前倾 / 后倾反馈增益 | 0 / 0 |

30°是目标请求，受每拍变化速率和提前回位影响，不表示实际必然达到30°。角度正负依赖已确认的本机安装方向。[完整定义](progress/2026-10-23/README.md)

连续2、3、5轮逐轮执行完整的准备、动作、回位和保持，默认仍为1轮。多轮扩展已完成离线验证，实机稳定性与距离待验证。**本次便携公开包从原运行链路提取并完成离线检查，实机视频来自此前原运行版本。**

## 研发与社区

RDK X5 Duck是主线；陆吾XGO-Duck用于独立平台对照，南瓜鸭用于外观与互动探索。后续推进连续短步、起停重复性、实时策略和V2的Module机内集成。[后续路线](ROADMAP.md)

在团队支持下，由**CanNyCat（GitHub：Xiaomiju-x）主导项目推进与实机集成**。欢迎在[地瓜社区](https://forum.d-robotics.cc/t/topic/35728)交流，在[Issues](https://github.com/Xiaomiju-x/rdk-x5-microduck/issues)提交结构版本、供电、参数和观察结果。

项目基于[Pollen Robotics Microduck](https://github.com/pollen-robotics/microduck)、[Microduck RL](https://github.com/pollen-robotics/microduck_rl)及[机械行者Robo / fanhao375 FT CAD](https://github.com/fanhao375/microduck-replica-cad)等开源成果。新增软件Apache-2.0，机械衍生件与媒体分别遵循[来源与许可](NOTICE.md)。

## 历史资料

[9月29日源码归档](microduck-source-20260929.zip)、[桌面阶段视频](milestone-20260929.mp4)、[前倾与承重案例](pitfall-loaded-tracking.mp4)、[动作切换案例](pitfall-policy-transition.mp4)保留供研究。根目录早期模块和旧ZIP为历史版本；新部署统一从 `software/` 开始。

[旧README](history/README_20261023.md) · [旧路线图](history/ROADMAP_20261023.md) · [完整研发记录](BUILD_LOG.md)
