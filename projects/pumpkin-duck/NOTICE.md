# 来源、许可与归档范围

项目：Pumpkin Duck Garden / 南瓜鸭瓜园。结项：2026-10-30。

由周苓萱（Lingxuan Zhou / CanNyCat，GitHub Xiaomiju-x）在团队支持下推进。本体延续 RDK X5 Duck 与其上游来源；本副线新增南瓜附件、桌面场景与对应展示资料。

## 分类许可

- 本目录原创说明文字、状态描述和独立交互设想按仓库 [Apache-2.0](../../LICENSE) 分享。
- `media/` 的实拍照片按 **CC BY-NC-SA 4.0** 分享，署名“RDK X5 MicroDuck 项目 / 周苓萱（CanNyCat）”。使用此前去除定位元数据的展示副本；本次未改变图像像素，不含 AI 合成图。
- `mechanical/mask/` 的 FT 接口衍生 STEP/STL 与其机械说明按 **CC BY-NC-SA 4.0** 分享，保留机械行者Robo / fanhao375、Pollen Robotics 与本项目改动的署名。它们是既有原型几何快照，不是新验证的标准化产品。
- 相机、语音模块、舵机、开发板与其他第三方品牌/底层硬件权利仍归各权利人；本目录不授予其商品设计或商标权利。

## 上游与复用

| 来源 | 关系 |
|---|---|
| [Pollen Robotics Microduck](https://github.com/pollen-robotics/microduck) | 原机器人生态与外形/运动参考 |
| [Microduck RL](https://github.com/pollen-robotics/microduck_rl) | 仿真与训练生态参考；本目录不重新分发其策略权重 |
| [机械行者Robo / fanhao375 FT CAD](https://github.com/fanhao375/microduck-replica-cad) | 本机 FT 结构与附件适配参考；未把上游本体计为南瓜副线原创 |
| [RDK X5 Duck](../../README.md) | 本体主线软件、历史短距实拍和既有开源资料 |

本次选择的面具修正：R1a 相机接口让位、R1b 平语音托板、R1c 双完整孔前抱箍。具体来源文件与 SHA256 见 [manifest](mechanical/mask/manifest.json)，原始文件字节保持。未重新打包整套第三方 CAD、训练权重、引擎或插件。

仓库整体来源与许可见[根 NOTICE](../../NOTICE.md)。[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)。原型功能和限制见[结项状态](STATUS.md)。
