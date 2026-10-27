# FT 本体选定打印件：28 个硬质零件

这是与 R8A 机载增量件配套的 **FT / HD1910M 本体选件**。文件来自本项目已冻结的 FT 打印准备网格，这次未改尺寸、孔位或形状；逐件与冻结记录的 SHA-256 相同。上游图纸由机械行者Robo建模、fanhao375整理，基于 Pollen Robotics MicroDuck 生态。

## 直接打印这套时，拿哪些文件

1. 本目录 **28 个 STL，每个文件打印 1 件**，包含面板和眼圈。`Gxx` 是本项目整理组，三位数字是来源对象编号，均不是舵机 ID。
2. 另取 `../r8a_parts/`：L1×1、L2×1、S1 6mm隔套×4，共6个实体。L1替代上游052底板，**不要再补一块052叠上去**。
3. 另取 `../tpu_soles/` 左右脚垫各1。PLA硬件共34个实体，TPU脚底2个；可选软嘴不计入本次基准。
4. 先按打印机、耗材、支撑重新切片，再逐盘打印。这里的STL不带打印方向或机器G-code；下表是分组建议，不是必须使用六张实际打印盘。

| 分组 | 文件编号 | 数量 | 含义 |
|---|---|---:|---|
| G01 髋与头内支撑 | 016、019、027、054、059、082、085 | 7 | 027要留到头部；两份同形髋转接/压盖分别用于左右 |
| G02 双腿 | 069、071、073、075、077、078、084、086 | 8 | 右踝069/左踝071；右大腿073/左大腿075；两片加固板、两小腿各1 |
| G03 硬脚掌 | 012、014 | 2 | 左右各1，不能用TPU脚底替掉硬脚掌 |
| G04 头壳与面板 | 010、050、056 | 3 | 下壳、上壳、面板；头盖最后合 |
| G05 颈头连接 | 021、029、031、032、034、080 | 6 | 下巴、U架、两连接片、眼圈、转接架 |
| G06 躯干外壳 | 023、038 | 2 | 左右各1，装配接线完成后合壳 |

完整52对象的取舍见 [FT_PRINT_SELECTION.csv](../../docs/FT_PRINT_SELECTION.csv)。它列出旧踝、旧压盖、轮滑件、原电控附件为何不打印，不要求读者自己在混合3MF中猜。

## 打印与装配

单位为mm。结构基线使用PLA、0.4mm喷嘴、0.2mm层高。按受力方向摆件，检查支撑、悬空、小孔与运动间隙；不将所有件简单平铺后发送。历史本体准备工艺为6墙/15%填充/树支撑，可作首轮切片起点，但应针对自己的机器核对。

这些文件保持冻结几何，包含已有实装发现和版本边界，**并非新一轮公差、承力或全行程认证**。尤其髋部舵盘侧、踝部轴承和头内装配顺序，请按 [装配教程](../../ASSEMBLY.md) 检查，出现不能自然落位时先核对版本及舵盘，不强行夹紧。

## 可编辑模型和来源

- 固定FT基线：[22ecf4daea158f2dfad7b633f730a5c04f1e04e0](https://github.com/fanhao375/microduck-replica-cad/tree/22ecf4daea158f2dfad7b633f730a5c04f1e04e0)
- SolidWorks源文件：[v2.0 / SolidWorks-FT.zip](https://github.com/fanhao375/microduck-replica-cad/releases/download/v2.0/SolidWorks-FT.zip)
- 9份改动STEP：[v2.0 / STEP-changed-parts-FT.zip](https://github.com/fanhao375/microduck-replica-cad/releases/download/v2.0/STEP-changed-parts-FT.zip)
- 本目录来源、尺寸、文件哈希：[manifest.json](manifest.json)

部分冻结网格来自已发布STEP重新网格化，部分保留原FT 3MF闭合网格；详见manifest中的`source_kind`和`source_name`。本次只复制这些已冻结网格，没有把STL转换伪称为参数化CAD。上游后续版本不自动混入本基线。

本目录按 **CC BY-NC-SA 4.0** 共享。署名：机械行者Robo / fanhao375（FT CAD），Pollen Robotics（MicroDuck生态），RDK X5 MicroDuck项目 / CanNyCat（选件与打印准备）。同形副本保留各自编号便于装配追溯。许可见[NOTICE](../../NOTICE.md)。
