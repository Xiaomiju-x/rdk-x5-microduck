# 文件、证据与本地归档范围

本公开目录是**精选结项档案**，不是所有本地工程的镜像，也不是经过完整实物验证的量产制造包。

## 本次随仓库公开

| 路径 | 内容 | 属性 |
|---|---|---|
| [README.md](README.md) / [README.en.md](README.en.md) | 中英文结项总览 | 已结项，停止主动开发 |
| [STATUS.md](STATUS.md) / [status.json](status.json) | 实物/数字状态与冻结版本 | 不用软件通过冒充实机通过 |
| [EXTENSIONS.md](EXTENSIONS.md) | 面具感知/表达与瓜园互动拓展 | 未完成设计，仅保留，不排期 |
| [MECHANICAL_NOTES.md](MECHANICAL_NOTES.md) | 驱动侧、从动盘及接口净空等问题 | 明确未修复/未验收 |
| [mechanical/mask/](mechanical/mask/) | 九个面具选件的 STEP/STL，含试配片 | 既有修正件原样归档；不是完整整机制造包 |
| [media/](media/) | 六张实拍照片 | 已有展示副本，GPS 元数据已去除，图像扫描/像素未因本次归档修改 |
| [NOTICE.md](NOTICE.md) | 来源、许可及范围 | 按文字、照片、几何分类 |

照片均为 2026-10-28 收到并用于展示材料的实物图片，照片本身不证明电动联调完成：

| 文件 | 展示内容 |
|---|---|
| [duck-and-mask.jpg](media/duck-and-mask.jpg) | 机器鸭与面具 |
| [pumpkin-mask.jpg](media/pumpkin-mask.jpg) | 南瓜面具细节 |
| [complete-scene.jpg](media/complete-scene.jpg) | 实物全景 |
| [hatching.jpg](media/hatching.jpg) | 孵化机构 |
| [phantom-grille.jpg](media/phantom-grille.jpg) | 幻影格栅 |
| [five-petal-box.jpg](media/five-petal-box.jpg) | 五瓣宝盒 |

历史主线运动视频复用仓库已有[原片](../../media/20261023/onboard-short-walk.mp4)，不重复上传，不改动作顺序或改写配置。

## 本地完整保留，未在本次全部上传

| 类别 | 保留内容 |
|---|---|
| 机械与装配 | R1 面具原生快照、闭合孔/接口/语音修正、D2.1 原 21 盘制造文件、已交付单件修正和完整装配 HTML；旧件/返工原因不删除 |
| 桌面电气 | 独立 X5 接线单、A4 纸片、五舵机编号/照片对应、调试网页及日志；不把其发布为默认可连接任何机器的控制器 |
| 数字展示 | Web 工程和本地入口、UE5 Overlay18 独立包与旧封存包、截图、完整路线与性能回执 |
| 仿真训练 | 源码、模型合同、策略候选、逐段动作来源、失败与 93/100 扰动结果；不宣称统一策略合格 |
| 展示材料 | 中文和英文四项材料文件夹、独立作品 PPT、Group 03 官方终稿、中英五版 A4 讲稿及现有 Demo |

本地结项入口另行索引这些文件并记录 SHA256。主办方含其他组内容的整份终稿、内部原始工作日志、内网配置、完整第三方资源与大体积游戏包没有混入本公开目录。已有本地交付文件和桌面快捷入口保持可用，本次不重新生成游戏或旧制造包。

本次修改随默认分支保留；[固定主线 v2026.10.27.1](https://github.com/Xiaomiju-x/rdk-x5-microduck/releases/tag/v2026.10.27.1)不包含这次新增目录，请使用当前目录或本次提交的固定链接。

归档固定快照：[pumpkin-duck-closeout-20261030](https://github.com/Xiaomiju-x/rdk-x5-microduck/tree/pumpkin-duck-closeout-20261030/projects/pumpkin-duck)。该标签用于本副线资料留存，不是新的主线运行/制造 Release。
