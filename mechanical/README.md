# RDK Duck 机载结构增量包 · R8A

本目录提供当前X5下部支架和FT脚垫，整机原CAD从[机械行者Robo / fanhao375 FT仓库](https://github.com/fanhao375/microduck-replica-cad)获取。本包不包含旧远悬重背包、不包含商品板卡的厂家模型。

## 文件与数量

| 文件 | 数量 | 说明 |
|---|---:|---|
| `r8a_parts/L1_R8_short_FT_root.step` / `.stl` | 1 | 替换FT躯干底座的短根座，保留原四孔和接口，短梁朝后 |
| `r8a_parts/L2_R8_flat_battery_portrait_X5.step` / `.stl` | 1 | 平电池托指和竖X5架；已做R8A下方螺母装入开槽，文件内仍保留R8零件名 |
| `r8a_parts/S1_R8_PCB_spacer_6mm.step` / `.stl` | 4 | 6mm隔套；不能混用旧8mm隔套 |
| `cad/R8A_print_parts.FCStd` | 1 | 六个独立BRep实体的可编辑FreeCAD文档，无厂家板卡、无电池占位；**没有草图/特征构造历史** |
| `cad/R8A_print_parts.step` | 1 | 同六实体的中性格式，可导入机械CAD；各零件在装配坐标中 |
| `tpu_soles/G07_046_sole.stl` | 1 | FT左脚垫；原几何，无变形缩放 |
| `tpu_soles/G07_048_sole.stl` | 1 | FT右脚垫；原几何，无变形缩放 |

STL为mm单位并按打印件坐标导出。STEP/FCStd为实体编辑用途，不把BRep实体文档宣称为完整参数化设计树。脚垫的可编辑上游SolidWorks源件在作者FT源CAD包中，本次只提供用于本机TPU打印的两只STL。

## 打印项目

- [R8A六件一盘，P1S / PLA](print_projects/R8A_SIX_PARTS_P1S_PLA.3mf)：L1×1、修正L2×1、隔套×4。沿原R8排布/配置替换为已核对的R8A L2；每个对象与本目录STL坐标网格一致，ZIP CRC通过。
- [仅替换L2，P1S / PLA](print_projects/MicroDuck_R8A_L2_ONLY_PLA.3mf)：已经有L1和隔套时使用。
- [两脚垫一盘，P1S / TPU95A HF](print_projects/RDK_FT_LEFT_RIGHT_SOLES_P1S_TPU95AHF.3mf)：左右各一只；外置料架，不使用AMS。

三个文件都是**可编辑3MF，需在自己的切片器中重新切片并检查预览**，不是可直接发送的G-code。工艺基线：P1S、0.4mm喷嘴、纹理PEI、0.2mm层高。改机器/喷嘴/材料必须重设。更多参数与安装顺序见[装配说明](../ASSEMBLY.md)。本轮没有发送打印，包检查不代替实物公差、承载和运动净空验证。

## 设计尺寸与装配边界

- 下电池按70×40×19mm占位设计，70mm沿左右、40mm沿前后、19mm高；托指加薄泡棉与绑带。
- X5四孔约49×58mm，四个6mm隔套，M2×12+普通六角M2螺母。下方螺母从上方开口装入。
- L1/L2以两套M3×16连接，孔中心间距64mm；L1复用原FT尾端四处连接。
- 成功实拍中两电池分置躯干两侧，微雪贴在其中一块外侧，前下方还存在棕色附加件；这些没有包含在本CAD中。历史R8“顶部平叠/下部托盘电池”占位不等于成功当天的精确实装布局。
- 不把电池或PCB固定到活动头颈、腿部。线束、真实螺钉公差与全行程碰撞须在自己的机器上核对。

## 归属、许可与修改说明

上游来源：[Pollen MicroDuck](https://github.com/pollen-robotics/microduck)、[MicroDuck RL](https://github.com/pollen-robotics/microduck_rl)、[机械行者Robo / fanhao375 FT CAD](https://github.com/fanhao375/microduck-replica-cad)。本机FT参考提交 `22ecf4daea158f2dfad7b633f730a5c04f1e04e0`。

本目录CAD、STEP、STL、3MF和对应几何图按 **CC BY-NC-SA 4.0（署名—非商业性使用—相同方式共享）** 发布。保留FT底座接口的L1属于衍生设计；本项目新增X5托架/隔套同样采用该许可便于整套复用。046/048脚垫保留上游原形状，本项目仅准备TPU工艺及打印摆放。请署名“机械行者Robo / fanhao375（FT结构），Pollen Robotics（上游MicroDuck生态），RDK X5 MicroDuck项目 / CanNyCat（X5集成与R8A修改）”。不将这些结构文件笼统称为Apache或无限制商用。

R8A相对R8只对L2下方两个M2螺母槽增加上方装入通道，X5孔位、L1和隔套几何未变。公开FCStd/装配STEP从已保存R8A模型中提取六个打印实体，剔除厂家板卡和电池占位；独立重开验证六实体有效。文件校验和见[manifest.json](manifest.json)，CAD检查见[cad/cad_check.json](cad/cad_check.json)。
