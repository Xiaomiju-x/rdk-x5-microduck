# 仿真模型来源与许可

本目录的 Python 程序由 RDK X5 MicroDuck 项目 / CanNyCat 编写，采用仓库根目录 Apache-2.0 许可。

`model/` 的 XML、STL 及其派生渲染图片/视频采用 **CC BY-NC-SA 4.0**：
https://creativecommons.org/licenses/by-nc-sa/4.0/

保留以下归属：

- Pollen Robotics：Microduck 原始机器人与模型生态。
- 机械行者Robo：飞特版 SolidWorks 重建与结构建模。
- fanhao375：复刻 CAD 的整理和分发。
- CanNyCat / RDK X5 MicroDuck 项目：FT 网格分组、凸包简化、关节树和 MuJoCo 教学环境适配。

固定的上游 CAD 来源及许可声明：
https://github.com/fanhao375/microduck-replica-cad/blob/22ecf4daea158f2dfad7b633f730a5c04f1e04e0/README.md#声明与许可

上游 CAD 是几何来源；本目录不是上游提供的原生 MuJoCo 模型。项目将 FT CAD 显示网格按刚体分组，以凸包简化，建立15个转动关节及14个位置执行器。几何文件不保留原始零件的全部内腔、电子器件细节或 CAD 参数历史。

此次公开适配移除了旧研究模型的胸前/后低位载荷假设，保留裸机总质量基线、近似初始姿态、估计惯量和理想PD，添加地面、灯光和演示程序；修正凸包 STL 的三角形绕序与法线以用于实体渲染，顶点坐标保持。来源哈希、变更清单和每个文件哈希见 `model/manifest.json`。

本模型不包含成功视频中两侧电池、X5、微雪、安装件或棕色附加件，也不携带实机绝对舵机坐标、校准数据或神经网络权重。模型的表面、质量、初始姿态、接触和执行器参数均不能代替本机测量。名字相同不表示与 XL330、陆吾或实机电机参数兼容。

如继续分发或修改模型及派生几何图，请保留署名、许可及修改说明。涉及商品板卡或舵机外观的品牌权利不由本项目授予。
