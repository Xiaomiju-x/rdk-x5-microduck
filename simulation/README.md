# FT 教学仿真：先跑通模型与物理循环

完整环境、逐步命令、结果解释和后续 RL 研究入口见 [SIMULATION.md](../SIMULATION.md)。

此目录仅在电脑运行 MuJoCo，不连接 X5、串口或真实舵机。它展示 FT 几何、自由基座保持与悬空关节响应；**不是 D 动作的仿真验收，也不是已经训练好的行走策略**。

![FT裸机教学模型](media/ft-reference.png)

[2秒悬空关节教学视频（躯干固定，非行走）](media/ft-joint-teaching.mp4)

从本目录执行：

```sh
python -m pip install -r requirements.txt
python -m unittest -v test_simulation
python run.py inspect
python run.py hold --seconds 2 --output .local/hold.json
python run.py joint --seconds 2 --output .local/joint.json
```

后三项不需要图形桌面；可视化另加 `--viewer` 或 `--image .local/preview.png`。

模型来源、许可和简化见 [NOTICE.md](NOTICE.md)，发布时实际运行结果见 [verification/](verification/)。
