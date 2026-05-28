from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from math import sin
from time import sleep


@dataclass(frozen=True)
class SimulationSummary:
    model_path: Path
    steps: int
    nq: int
    nv: int
    nu: int
    final_time: float
    final_qpos: tuple[float, ...]


def _load_mujoco():
    try:
        import mujoco
    except ImportError as exc:
        raise RuntimeError(
            "MuJoCo is not installed. Run scripts\\setup_python.ps1 first, "
            "or install the 'sim' extra."
        ) from exc
    return mujoco


def run_model(
    model_path: str | Path,
    *,
    steps: int = 1000,
    viewer: bool = False,
    realtime: bool = False,
) -> SimulationSummary:
    mujoco = _load_mujoco()
    path = Path(model_path).resolve()
    if not path.exists():
        raise FileNotFoundError(path)

    model = mujoco.MjModel.from_xml_path(str(path))
    data = mujoco.MjData(model)

    if viewer:
        import mujoco.viewer

        with mujoco.viewer.launch_passive(model, data) as handle:
            for step in range(steps):
                _apply_demo_control(data, step)
                mujoco.mj_step(model, data)
                handle.sync()
                if realtime:
                    sleep(float(model.opt.timestep))
    else:
        for step in range(steps):
            _apply_demo_control(data, step)
            mujoco.mj_step(model, data)
            if realtime:
                sleep(float(model.opt.timestep))

    return SimulationSummary(
        model_path=path,
        steps=steps,
        nq=int(model.nq),
        nv=int(model.nv),
        nu=int(model.nu),
        final_time=float(data.time),
        final_qpos=tuple(float(x) for x in data.qpos.copy()),
    )


def _apply_demo_control(data, step: int) -> None:
    if data.ctrl.size == 0:
        return
    phase = step * 0.02
    for index in range(data.ctrl.size):
        data.ctrl[index] = 0.25 * sin(phase + index)
