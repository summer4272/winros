# WinROS

**Windows-first ROS 2 robot learning workbench.**

WinROS 的目标很直接：让初学者、个人爱好者和小实验室可以先在 Windows 上跑通
ROS 2、MuJoCo 仿真、强化学习策略预览、VLA dry-run 和真机接口骨架，再逐步进入
Linux 集群、真实机器人和更复杂的研究系统。

很多人不是不想学机器人，而是卡在第一步：Linux 环境、VMware、GPU 直通、ROS 2
工作区、仿真器、训练脚本、真机安全边界同时出现。WinROS 想把这条路拆成可见、
可跑、可复现的步骤。

## 首屏 Demo

下面的视频展示了当前平台已经跑通的三条训练结果：人形机器人快跑、机器狗快跑、
机器狗上楼梯。三个片段都来自本地最新已训练权重的推理录制，并通过 WinROS 的中文
展示界面合成为 GitHub 首屏素材。

<p align="center">
  <a href="docs/assets/demo/winros_showcase.webm">
    <img src="docs/assets/demo/winros_showcase_poster.jpg" alt="WinROS 平台演示视频封面" width="960">
  </a>
</p>

中文展示页：[docs/demo/index.html](docs/demo/index.html)  
Demo 说明：[docs/DEMO.md](docs/DEMO.md)  
验证记录：[docs/VALIDATION.md](docs/VALIDATION.md)

## 为什么这个开源有意义

| 痛点 | WinROS 的做法 | 现在的证据 |
| --- | --- | --- |
| 初学者装环境太重 | Windows 原生入口，先跑 dashboard、仿真和 dry-run | [中文快速开始](docs/QUICKSTART_ZH.md) |
| RL 结果很难被信任 | 保留录制脚本、验证清单和 demo manifest | [验证记录](docs/VALIDATION.md) |
| ROS 2、仿真、学习代码割裂 | 一个仓库串起 CLI、Dashboard、MuJoCo、ROS 2 包和训练脚本 | [架构说明](docs/ARCHITECTURE.md) |
| VLA 和真机接入风险高 | VLA 先输出结构化命令，真机适配器默认 dry-run | [VLA 接口](docs/VLA_INTERFACE.md)、[真机接口](docs/REAL_ROBOTS.md) |
| 开源项目容易只放代码 | 提供初学者路线、贡献入口、复现边界和 roadmap | [为什么做 WinROS](docs/WHY_WINROS.md) |

## 现在可以做什么

- 打开中文图形化控制台，选择仿真、RL smoke test、VLA dry-run、ROS 2 build 等配置。
- 运行最小 MuJoCo 仿真，确认本机图形、Python 和依赖链路可用。
- 预览已经训练好的 Unitree G1 / Go2 locomotion 策略结果。
- 使用 VLA provider 接口把自然语言任务转成可验证的结构化机器人命令。
- 构建 ROS 2 workspace，测试 WinROS 自定义消息、服务、动作和 adapter 节点。
- 在不提交私有权重、SDK、数据集的前提下，把公开平台开源出去。

## 10 分钟开始

创建环境：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_conda_env.ps1
. .\scripts\activate_winros.ps1
```

打开图形化界面：

```powershell
python -m winros --dashboard
```

浏览器打开终端里打印的地址，通常是：

```text
http://127.0.0.1:8765
```

运行一个最小仿真：

```powershell
python -m winros --list-robots
python -m winros --robot two_link_arm --steps 1000
```

测试 VLA dry-run：

```powershell
python -m winros --vla-provider rules --vla-robot "Unitree Go2" --vla-instruction "walk forward slowly"
```

更完整的新手路线见：[docs/BEGINNER_PATH.md](docs/BEGINNER_PATH.md)。

## 仓库结构

```text
.
|-- apps/dashboard/       # Dashboard 使用说明
|-- configs/              # 平台、任务、资产、dashboard 配置
|-- docs/                 # 架构、验证、demo、roadmap、接口文档
|-- requirements/         # 安装依赖分组
|-- ros2_ws/              # ROS 2 interface、MuJoCo bridge、robot adapter
|-- scripts/              # Windows helper scripts 和 demo 录制脚本
|-- sim/                  # MuJoCo 模型和仿真资源
|-- src/winros/           # Python CLI、Dashboard、RL、VLA、sim utilities
`-- tests/                # 轻量测试
```

## 文档入口

| 文档 | 用途 |
| --- | --- |
| [为什么做 WinROS](docs/WHY_WINROS.md) | 面向 GitHub 访客的项目价值说明 |
| [中文快速开始](docs/QUICKSTART_ZH.md) | 从零跑 dashboard、仿真、VLA dry-run |
| [初学者路线](docs/BEGINNER_PATH.md) | 10 分钟、30 分钟、1 小时分别能做什么 |
| [Demo 展示素材](docs/DEMO.md) | 如何重新录制和合成首屏视频 |
| [验证记录](docs/VALIDATION.md) | 当前 demo、测试、复现清单 |
| [Dashboard](docs/DASHBOARD.md) | 图形化控制台和自定义 profile |
| [VLA Interface](docs/VLA_INTERFACE.md) | VLA provider、命令结构和安全校验 |
| [Real Robots](docs/REAL_ROBOTS.md) | 真机 adapter 的 dry-run、安全门控和遥测 |
| [Roadmap](docs/ROADMAP.md) | 平台后续方向 |

## Safety Model

WinROS 对仿真、VLA、RL 和真机使用同一条安全原则：

1. 先生成结构化命令。
2. 再做范围、模式、硬件状态校验。
3. 最后才允许发布到 ROS 2 或真机 adapter。

真实机器人默认不开放控制。新的硬件 adapter 必须先支持 dry-run、遥测、限幅、急停或
watchdog，再进入真实执行路径。

## 开源边界

仓库默认不提交：

- 训练 checkpoint、实验日志、评测视频原始缓存；
- `third_party/` 下载的第三方仓库；
- 私有机器人 SDK、IP、标定文件和密钥；
- 未确认授权的数据集、大模型权重和商业资产。

可公开的内容放在代码、配置、文档、接口、复现脚本和轻量 demo 素材中。这样项目可以
开源、可学习、可复现，也不会把未来接真机时的风险一起公开扩散。

## License

MIT. Third-party assets, datasets, model weights, robot SDKs, and private
calibration files keep their own licenses and should stay outside Git unless
redistribution is explicitly allowed.
