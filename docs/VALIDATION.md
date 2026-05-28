# WinROS 验证记录

这份文档回答一个开源项目最容易被问的问题：它现在到底跑通了什么？

当前验证日期：2026-05-28

最近一次本地检查：

- `python -m pytest`：10 passed, 4 skipped
- `python -m py_compile .\scripts\build_showcase_demo.py .\scripts\record_unitree_mjlab_demo.py`：passed
- `python -m json.tool .\docs\assets\demo\manifest.json`：passed

## GitHub 首屏 Demo

| 展示项 | 机器人 | 任务 | 输出文件 | 来源 |
| --- | --- | --- | --- | --- |
| 人形机器人快跑 | Unitree G1 | FastRunV1 | `docs/assets/demo/g1_fast_run.mp4` | 最新本地 checkpoint 推理录制 |
| 机器狗快跑 | Unitree Go2 | FastFlat | `docs/assets/demo/go2_fast_run.mp4` | 最新本地 checkpoint 推理录制 |
| 机器狗上楼梯 | Unitree Go2 | StairsForwardV3 | `docs/assets/demo/go2_stairs.mp4` | 最新本地 checkpoint 推理录制 |
| 平台展示视频 | WinROS dashboard mock showcase | 三路合成 | `docs/assets/demo/winros_showcase.webm` | `scripts/build_showcase_demo.py` |

机器可读记录见：

```text
docs/assets/demo/manifest.json
```

## 当前录制使用的 checkpoint

这些路径来自本地训练目录，不提交到 Git：

- `D:\winros\third_party\unitree_rl_mjlab\logs\rsl_rl\g1_velocity\2026-05-27_20-30-43_unitree_g1_fast_run_v1_20260527_203014\model_22998.pt`
- `D:\winros\third_party\unitree_rl_mjlab\logs\rsl_rl\go2_velocity\2026-05-27_00-46-23_unitree_go2_fast_flat_20260527_004601\model_11999.pt`
- `D:\winros\third_party\unitree_rl_mjlab\logs\rsl_rl\go2_velocity\2026-05-28_01-36-34_unitree_go2_stairs_forward_v3_20260528_013607\model_8999.pt`

## 重新生成 Demo

```powershell
python .\scripts\record_unitree_mjlab_demo.py --profile all --steps 240
python .\scripts\build_showcase_demo.py
```

第一条命令会从 `D:\winros\third_party\unitree_rl_mjlab` 中寻找最新匹配 checkpoint 并重新
录制三个源视频。第二条命令会合成 GitHub 首屏视频、封面图和 demo manifest。

## 发布前检查

```powershell
python -m pytest
python -m py_compile .\scripts\build_showcase_demo.py .\scripts\record_unitree_mjlab_demo.py
python -m json.tool .\docs\assets\demo\manifest.json
```

手动检查：

- 打开 `docs/demo/index.html`，确认四个视频都能加载和播放；
- 打开 dashboard，确认配置、profile、dry-run 状态显示正常；
- 确认 `runs/`、`third_party/`、checkpoint、SDK、密钥没有进入 Git；
- 确认 README 首屏封面和 demo 链接可点击。

## 验证原则

WinROS 的验证优先证明平台链路，而不是追求单个模型指标：

1. 初学者能打开 dashboard。
2. 仿真能运行。
3. 训练结果能被录制和展示。
4. VLA 命令先 dry-run。
5. ROS 2 和真机接口有清晰边界。
6. 公开仓库不包含私有权重和危险硬件配置。
