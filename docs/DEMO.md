# Demo 展示素材

这个目录下的素材用于 GitHub 首屏展示：

- `docs/assets/demo/winros_showcase.webm`：合成后的 8 秒中文平台展示视频；
- `docs/assets/demo/winros_showcase_poster.jpg`：README 首屏封面图；
- `docs/assets/demo/g1_fast_run.mp4`：人形机器人快跑；
- `docs/assets/demo/go2_fast_run.mp4`：机器狗快跑；
- `docs/assets/demo/go2_stairs.mp4`：机器狗上楼梯；
- `docs/demo/index.html`：中文静态展示页。
- `docs/assets/demo/manifest.json`：机器可读 demo 元数据，记录视频、公开运行标识和验证状态。

重新生成展示视频：

```powershell
python .\scripts\record_unitree_mjlab_demo.py --profile all --steps 240
python .\scripts\build_showcase_demo.py
```

如果后续换成更好的推理结果，只要替换 `docs/assets/demo/` 里的三个源视频，再重新运行脚本即可。

建议每次公开发布前同时检查：

```powershell
python -m json.tool .\docs\assets\demo\manifest.json
```

并更新 `docs/VALIDATION.md` 中的公开运行标识和验证说明。

当前公开记录的训练运行标识：

- G1 快跑：`g1_velocity/2026-05-27_20-30-43_unitree_g1_fast_run_v1_20260527_203014/model_22998.pt`
- Go2 快跑：`go2_velocity/2026-05-27_00-46-23_unitree_go2_fast_flat_20260527_004601/model_11999.pt`
- Go2 上楼梯：`go2_velocity/2026-05-28_01-36-34_unitree_go2_stairs_forward_v3_20260528_013607/model_8999.pt`
