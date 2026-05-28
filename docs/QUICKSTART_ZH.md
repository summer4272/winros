# WinROS 中文快速开始

WinROS 的目标是让初学者可以在 Windows 上先跑通 ROS 2、MuJoCo、强化学习仿真和
dry-run 真机接口，再逐步接入 VLA、数据采集和真实机器人。

如果你是第一次打开这个项目，建议先看：

- [为什么做 WinROS](WHY_WINROS.md)
- [初学者路线](BEGINNER_PATH.md)
- [验证记录](VALIDATION.md)

## 1. 创建环境

在仓库根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_conda_env.ps1
. .\scripts\activate_winros.ps1
```

## 2. 打开图形化界面

```powershell
python -m winros --dashboard
```

浏览器打开终端里打印的地址，通常是：

```text
http://127.0.0.1:8765
```

Dashboard 里可以直接选择仿真、RL smoke test、VLA dry-run、ROS 2 build 和
Unitree 研究训练脚本。默认不开放真实硬件控制。

## 3. 跑一个最小仿真

```powershell
python -m winros --robot two_link_arm --steps 1000
```

## 4. 测试 VLA dry-run

```powershell
python -m winros --vla-provider rules --vla-robot "Unitree Go2" --vla-instruction "walk forward slowly"
```

它会输出结构化命令，但不会直接控制真机。

## 5. ROS 2 工作区

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_ros2_ws.ps1
. .\scripts\activate_ros2_winros.ps1
ros2 pkg list | findstr winros
```

## 开源注意

不要提交以下内容：

- `runs/` 里的训练日志和 checkpoint；
- `third_party/` 里下载的第三方仓库；
- 私有 SDK、机器人 IP、标定文件、密钥；
- 大模型权重和未确认授权的数据集。
