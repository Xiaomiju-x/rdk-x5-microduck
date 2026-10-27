# 来源、许可与发布范围

更新：2026-10-27。当前运行入口为`software/`，打印件为`mechanical/`，离线教学仿真为`simulation/`。根目录旧模块和9月29日ZIP保留历史归属；不同类别资源按下述许可分别使用。

## 本项目新增代码

本仓库及源码ZIP中由本项目新增的Python/JS/HTML/CSS代码按Apache License 2.0公开，见 `LICENSE`。最新公开包提取了D相对目标、颈部时序和硬件执行流程，将地址、串口、站姿与安装角改为逐机配置。公开面板默认DEMO；本次整理不修改本机正在使用的调试控制器。

原创项目说明文字同样适用Apache-2.0。实拍照片与视频仅作为本项目研究/复现记录，按CC BY-NC-SA 4.0分享，署名“RDK X5 MicroDuck 项目 / CanNyCat”。涉及第三方外观与品牌的权利不由本许可授予，不意味着可据此销售上游产品。

## 上游归属

|来源|复用关系|本次处理|
|---|---|---|
|Pollen Robotics microduck / microduck_rl|机器人、仿真和策略生态|链接到官方，不重新打包权重或模型|
|机械行者Robo / fanhao375 microduck-replica-cad|本机FT结构与装配参考|完整本体与SolidWorks源件给上游入口；本包提供28个选定本体STL、FT接口衍生的R8A改件和两只原形状脚垫，按CC BY-NC-SA 4.0保留署名与修改说明|
|fanhao375 microduck-replica|复刻资料及总线工具|旧ZIP内reference_feetech.py及新software/vendor/feetech.py保留上游归属，附Apache-2.0许可；来源与文件核对见software文档|
|Rhoban Placo / Open Duck reference motion generator|常规运动学路线参考|只给入口，不宣称本阶段运行了自己的新训练|

CAD仓库版本及素材许可证应在下载时再次核对。源模型和作者图纸不是本项目原创，个人GitHub发布不改变其非商业性/相同方式共享条件。需要其他使用范围时应另行向权利人确认。

## 本次机械与图解

`mechanical/`中的CAD、STEP、STL、3MF及其几何图采用CC BY-NC-SA 4.0。L1保留FT底座接口，属于衍生设计；新增X5托架与隔套采用同一许可。046/048脚垫保持上游形状，本项目准备TPU打印配置。具体提交、修改范围和署名见`mechanical/README.md`，不把上游本体或商品板卡包装成本项目原创。

本项目独立绘制的系统架构和控制时序图随说明文字采用Apache-2.0；实拍媒体仍按上节CC BY-NC-SA 4.0。商品板卡只公开型号、接口和应用接线，不意味着本项目拥有其底层硬件设计权利。

## 本次新增本体选件与仿真

`mechanical/body_parts/` 的28个FT本体STL保留冻结来源几何，属于上游FT设计的复制/网格化准备，沿用CC BY-NC-SA4.0，不能记作本项目原创设计。逐件出处与哈希在该目录manifest中。新增FT装配关系渲染、带实拍的原型配置卡，按相应几何/实拍的CC BY-NC-SA4.0许可共享。

`simulation/model/` 的FT衍生MJCF与凸包几何、`simulation/media/` 渲染图像和视频采用CC BY-NC-SA4.0，保留机械行者Robo / fanhao375、Pollen Robotics与本项目建模改动的署名。Python示例和测试采用Apache-2.0。仿真是带明确物理假设的教学模型，不声称为成功样机的精确数字孪生。具体来源见 `simulation/NOTICE.md` 与 `simulation/model/manifest.json`。

独立绘制的系统框架、复刻流程和机体坐标SVG/PNG随说明文字按Apache-2.0分享。框架图不包含厂商未授权整板CAD。

## 本次未发布内容

个人凭据、SSH密钥、公司内部飞书链接、内网地址、设备序列号、其他项目内容、完整未审阅原始日志、第三方未经核对的二进制/权重。原视频不改，公开副本去除手机定位与设备元数据，保留完整时长和动作顺序。

## 完整来源链接

- https://github.com/pollen-robotics/microduck
- https://github.com/pollen-robotics/microduck_rl
- https://github.com/fanhao375/microduck-replica-cad
- https://github.com/fanhao375/microduck-replica
- https://github.com/fanhao375/microduck-replica/tree/master/tools/servo-web
- https://github.com/Rhoban/placo
- https://github.com/apirrone/Open_Duck_reference_motion_generator
- https://www.apache.org/licenses/LICENSE-2.0
- https://creativecommons.org/licenses/by-nc-sa/4.0/
