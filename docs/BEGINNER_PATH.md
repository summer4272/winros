# WinROS 初学者路线

这份路线面向第一次打开仓库的人。目标不是一次学完 ROS 2、强化学习和真机控制，而是
先看到平台能工作，再逐步理解每一层。

## 第 0 步：看一眼结果

先打开中文展示页：

```text
docs/demo/index.html
```

你会看到三段已经训练好的策略推理结果：

- 人形机器人 G1 快跑；
- 机器狗 Go2 快跑；
- 机器狗 Go2 上楼梯。

这一步的意义是确认 WinROS 不是空项目，它已经有能展示的机器人学习结果。

## 10 分钟：打开 dashboard

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_conda_env.ps1
. .\scripts\activate_winros.ps1
python -m winros --dashboard
```

打开终端打印的本地地址，通常是：

```text
http://127.0.0.1:8765
```

你应该能看到中文图形化界面。这里可以选择环境检查、仿真、RL smoke test、VLA dry-run、
ROS 2 build 和研究脚本。

## 30 分钟：跑一个最小仿真

```powershell
python -m winros --list-robots
python -m winros --robot two_link_arm --steps 1000
```

这一步确认 Python、MuJoCo 和 WinROS CLI 的基础链路可用。

## 45 分钟：试一次 VLA dry-run

```powershell
python -m winros --vla-provider rules --vla-robot "Unitree Go2" --vla-instruction "walk forward slowly"
```

输出应该是一条结构化机器人命令。它不会直接控制真实机器狗，目的是先验证“语言任务 ->
结构化命令 -> 安全检查”的接口形状。

## 60 分钟：构建 ROS 2 workspace

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_ros2_ws.ps1
. .\scripts\activate_ros2_winros.ps1
ros2 pkg list | findstr winros
```

你应该能看到 WinROS 的 ROS 2 packages。后续真机 adapter、仿真桥和遥测都沿着这条路径
扩展。

## 下一步可以怎么贡献

- 如果你是新手：补充安装问题、报错截图、快速开始文档。
- 如果你会前端：优化 dashboard 的布局、状态展示和自定义 profile 体验。
- 如果你会 RL：补充轻量 baseline、评测脚本和训练复现实验。
- 如果你会 ROS 2：完善消息、服务、动作和 bridge 节点。
- 如果你有真机：先贡献 dry-run adapter、遥测和安全限制，不直接提交真实控制逻辑。
