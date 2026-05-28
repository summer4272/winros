from __future__ import annotations

import json
import mimetypes
import os
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import yaml

from winros import __version__
from winros.asset_registry import list_assets
from winros.config import project_root
from winros.robot_registry import list_robots
from winros.task_registry import list_tasks


JsonMap = dict[str, Any]


@dataclass
class RunRecord:
    id: str
    profile_id: str
    title: str
    command: list[str]
    started_at: str
    stdout_path: Path
    stderr_path: Path
    pid: int | None = None
    process: subprocess.Popen | None = field(default=None, repr=False)
    returncode: int | None = None


RUNS: dict[str, RunRecord] = {}


DEFAULT_PROFILES: tuple[JsonMap, ...] = (
    {
        "id": "check_env",
        "title": "Environment Check",
        "group": "Setup",
        "mode": "dry_run",
        "summary": "Check Python, ROS 2, MuJoCo, CUDA, and common tools.",
        "template": [
            "{powershell}",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            "{root}\\scripts\\check_env.ps1",
        ],
        "params": [],
        "tags": ["setup", "safe"],
    },
    {
        "id": "sim_builtin",
        "title": "MuJoCo Built-In Sim",
        "group": "Simulation",
        "mode": "sim",
        "summary": "Run a small built-in MuJoCo model for a quick local smoke test.",
        "template": [
            "{python}",
            "-m",
            "winros",
            "--robot",
            "{robot}",
            "--steps",
            "{steps}",
        ],
        "params": [
            {
                "name": "robot",
                "label": "Robot",
                "type": "select",
                "default": "two_link_arm",
                "choices": ["two_link_arm", "differential_drive"],
            },
            {"name": "steps", "label": "Steps", "type": "int", "default": 500, "min": 1},
        ],
        "tags": ["sim", "safe"],
    },
    {
        "id": "preview_env",
        "title": "Random RL Rollout",
        "group": "Learning",
        "mode": "sim",
        "summary": "Run a short random-policy rollout in a registered training environment.",
        "template": [
            "{python}",
            "-m",
            "winros",
            "--env",
            "{env}",
            "--episodes",
            "{episodes}",
            "--steps",
            "{steps}",
        ],
        "params": [
            {
                "name": "env",
                "label": "Env",
                "type": "select",
                "default": "WinROSArmGrasp-v0",
                "choices": [
                    "WinROSArmGrasp-v0",
                    "WinROSQuadrupedLocomotion-v0",
                    "WinROSHumanoidLocomotion-v0",
                ],
            },
            {"name": "episodes", "label": "Episodes", "type": "int", "default": 1, "min": 1},
            {"name": "steps", "label": "Steps", "type": "int", "default": 300, "min": 1},
        ],
        "tags": ["rl", "safe"],
    },
    {
        "id": "train_arm_smoke",
        "title": "Arm RL Smoke Train",
        "group": "Learning",
        "mode": "training",
        "summary": "Train a tiny SAC run to validate the RL stack.",
        "template": [
            "{python}",
            "-m",
            "winros",
            "--train-env",
            "WinROSArmGrasp-v0",
            "--algo",
            "sac",
            "--timesteps",
            "{timesteps}",
            "--device",
            "{device}",
        ],
        "params": [
            {"name": "timesteps", "label": "Timesteps", "type": "int", "default": 128, "min": 1},
            {
                "name": "device",
                "label": "Device",
                "type": "select",
                "default": "cuda",
                "choices": ["cuda", "cpu"],
            },
        ],
        "tags": ["rl"],
    },
    {
        "id": "vla_dry_command",
        "title": "VLA Dry Command",
        "group": "VLA",
        "mode": "dry_run",
        "summary": "Convert a language instruction into a structured dry-run command.",
        "template": [
            "{python}",
            "-m",
            "winros",
            "--vla-provider",
            "rules",
            "--vla-robot",
            "{robot}",
            "--vla-instruction",
            "{instruction}",
        ],
        "params": [
            {"name": "robot", "label": "Robot", "type": "text", "default": "Unitree Go2"},
            {
                "name": "instruction",
                "label": "Instruction",
                "type": "text",
                "default": "walk forward slowly",
            },
        ],
        "tags": ["vla", "safe"],
    },
    {
        "id": "build_ros2_ws",
        "title": "Build ROS 2 Workspace",
        "group": "ROS 2",
        "mode": "dry_run",
        "summary": "Build WinROS ROS 2 packages with colcon.",
        "template": [
            "{powershell}",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            "{root}\\scripts\\build_ros2_ws.ps1",
        ],
        "params": [],
        "tags": ["ros2"],
    },
    {
        "id": "start_dry_adapter",
        "title": "Dry-Run Robot Adapter",
        "group": "Real Robot",
        "mode": "dry_run",
        "summary": "Start the ROS 2 adapter in dry-run mode.",
        "template": ["ros2", "run", "winros_robot_adapters", "dry_run_adapter"],
        "params": [],
        "tags": ["ros2", "hardware-gated"],
    },
    {
        "id": "go2_stairs_train",
        "title": "Go2 Stairs Train",
        "group": "Research Runs",
        "mode": "training",
        "summary": "Start the Go2 stairs-forward background training script.",
        "template": [
            "{powershell}",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            "{root}\\scripts\\start_unitree_stairs_v3_background.ps1",
            "-NumEnvs",
            "{num_envs}",
            "-Iterations",
            "{iterations}",
        ],
        "params": [
            {"name": "num_envs", "label": "Num envs", "type": "int", "default": 320, "min": 1},
            {
                "name": "iterations",
                "label": "Iterations",
                "type": "int",
                "default": 9000,
                "min": 1,
            },
        ],
        "tags": ["rl", "unitree"],
    },
    {
        "id": "g1_fast_run_train",
        "title": "G1 Fast Run Train",
        "group": "Research Runs",
        "mode": "training",
        "summary": "Start the G1 fast-run background training script.",
        "template": [
            "{powershell}",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            "{root}\\scripts\\start_g1_fast_run_v1_background.ps1",
            "-NumEnvs",
            "{num_envs}",
            "-Iterations",
            "{iterations}",
        ],
        "params": [
            {"name": "num_envs", "label": "Num envs", "type": "int", "default": 256, "min": 1},
            {
                "name": "iterations",
                "label": "Iterations",
                "type": "int",
                "default": 9000,
                "min": 1,
            },
        ],
        "tags": ["rl", "unitree"],
    },
    {
        "id": "play_unitree_latest",
        "title": "Play Unitree Latest",
        "group": "Research Runs",
        "mode": "sim",
        "summary": "Play the latest matching Unitree checkpoint.",
        "template": [
            "{powershell}",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            "{root}\\scripts\\play_unitree_mjlab_velocity_task_latest.ps1",
            "-Task",
            "{task}",
        ],
        "params": [
            {
                "name": "task",
                "label": "Task",
                "type": "select",
                "default": "Unitree-Go2-StairsForwardV3",
                "choices": [
                    "Unitree-Go2-StairsForwardV3",
                    "Unitree-G1-StairsForwardV1",
                    "Unitree-G1-FastRunV1",
                    "Unitree-G1-HurdlesRunV1",
                    "Unitree-Go2-FastFlat",
                    "Unitree-G1-FastFlatV2",
                ],
            }
        ],
        "tags": ["rl", "unitree"],
    },
)


def dashboard_config_path() -> Path:
    return project_root() / "configs" / "dashboard.yaml"


def dashboard_local_config_path() -> Path:
    return project_root() / "configs" / "dashboard.local.yaml"


def load_dashboard_config() -> JsonMap:
    config: JsonMap = {}
    for path in (dashboard_config_path(), dashboard_local_config_path()):
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}
        if not isinstance(loaded, dict):
            raise ValueError(f"Expected a mapping in {path}")
        config = _deep_merge(config, loaded)
    return config


def save_dashboard_local_config(data: JsonMap) -> Path:
    allowed = {
        key: data[key]
        for key in ("theme", "layout", "preferences")
        if key in data and isinstance(data[key], dict)
    }
    path = dashboard_local_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(allowed, handle, sort_keys=False, allow_unicode=True)
    return path


def collect_state() -> JsonMap:
    config = load_dashboard_config()
    return {
        "project": {
            "name": "WinROS",
            "version": __version__,
            "root": str(project_root()),
            "runsDir": str(project_root() / "runs"),
        },
        "config": config,
        "tasks": [_task_to_json(task) for task in list_tasks()],
        "robots": [_robot_to_json(robot) for robot in list_robots()],
        "assets": [_asset_to_json(asset) for asset in list_assets()],
        "envs": _safe_list_envs(),
        "profiles": [_public_profile(profile) for profile in list_profiles(config)],
        "runs": list_runs(),
    }


def list_profiles(config: JsonMap | None = None) -> list[JsonMap]:
    profiles = [dict(profile) for profile in DEFAULT_PROFILES]
    for custom in (config or {}).get("custom_profiles", []):
        if not isinstance(custom, dict):
            continue
        if not custom.get("id") or not custom.get("title") or not custom.get("command"):
            continue
        profile = {
            "id": str(custom["id"]),
            "title": str(custom["title"]),
            "group": str(custom.get("group") or "Custom"),
            "mode": str(custom.get("mode") or "dry_run"),
            "summary": str(custom.get("summary") or ""),
            "command": [str(item) for item in custom["command"]],
            "params": custom.get("params") if isinstance(custom.get("params"), list) else [],
            "tags": custom.get("tags") if isinstance(custom.get("tags"), list) else ["custom"],
        }
        profiles.append(profile)
    return profiles


def build_profile_command(
    profile_id: str,
    params: JsonMap | None = None,
    *,
    config: JsonMap | None = None,
) -> list[str]:
    profile = _find_profile(profile_id, config)
    if "command" in profile:
        template = [str(item) for item in profile["command"]]
    else:
        template = [str(item) for item in profile["template"]]

    values = _profile_values(profile, params or {})
    context = {
        "python": sys.executable,
        "powershell": _powershell_exe(),
        "root": str(project_root()),
        **values,
    }
    return [item.format(**context) for item in template]


def command_to_string(command: list[str]) -> str:
    return subprocess.list2cmdline([str(item) for item in command])


def launch_profile(profile_id: str, params: JsonMap | None = None) -> JsonMap:
    config = load_dashboard_config()
    profile = _find_profile(profile_id, config)
    if profile.get("mode") == "hardware":
        raise PermissionError("Hardware profiles must be enabled by a concrete adapter.")

    command = build_profile_command(profile_id, params, config=config)
    run_id = uuid.uuid4().hex[:12]
    log_dir = project_root() / "runs" / "dashboard"
    log_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = log_dir / f"{run_id}.out.log"
    stderr_path = log_dir / f"{run_id}.err.log"

    stdout_handle = stdout_path.open("w", encoding="utf-8")
    stderr_handle = stderr_path.open("w", encoding="utf-8")
    creationflags = 0
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        process = subprocess.Popen(
            command,
            cwd=project_root(),
            env=_subprocess_env(),
            stdout=stdout_handle,
            stderr=stderr_handle,
            text=True,
            creationflags=creationflags,
        )
    finally:
        stdout_handle.close()
        stderr_handle.close()

    record = RunRecord(
        id=run_id,
        profile_id=profile_id,
        title=str(profile["title"]),
        command=command,
        started_at=_now_iso(),
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        pid=process.pid,
        process=process,
    )
    RUNS[run_id] = record
    return run_to_json(record, include_tail=True)


def list_runs() -> list[JsonMap]:
    return [run_to_json(record) for record in RUNS.values()]


def run_to_json(record: RunRecord, *, include_tail: bool = False) -> JsonMap:
    status = "running"
    returncode = record.returncode
    if record.process is not None:
        poll = record.process.poll()
        if poll is not None:
            record.returncode = int(poll)
            returncode = record.returncode
    if returncode is not None:
        status = "succeeded" if returncode == 0 else "failed"

    data: JsonMap = {
        "id": record.id,
        "profileId": record.profile_id,
        "title": record.title,
        "pid": record.pid,
        "status": status,
        "returncode": returncode,
        "startedAt": record.started_at,
        "command": command_to_string(record.command),
        "stdoutPath": str(record.stdout_path),
        "stderrPath": str(record.stderr_path),
    }
    if include_tail:
        data["stdoutTail"] = _tail_file(record.stdout_path)
        data["stderrTail"] = _tail_file(record.stderr_path)
    return data


def stop_run(run_id: str) -> JsonMap:
    record = RUNS.get(run_id)
    if record is None:
        raise KeyError(run_id)
    if record.process is not None and record.process.poll() is None:
        record.process.terminate()
    return run_to_json(record, include_tail=True)


def run_dashboard(host: str = "127.0.0.1", port: int = 8765) -> int:
    server = _make_server(host, port)
    actual_host, actual_port = server.server_address
    print(f"WinROS dashboard: http://{actual_host}:{actual_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    finally:
        server.server_close()
    return 0


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "WinROSDashboard/0.1"

    def do_GET(self) -> None:  # noqa: N802
        try:
            parsed = urlparse(self.path)
            if parsed.path == "/api/state":
                self._send_json(collect_state())
                return
            if parsed.path == "/api/runs":
                self._send_json({"runs": list_runs()})
                return
            if parsed.path.startswith("/api/runs/"):
                run_id = parsed.path.rstrip("/").split("/")[-1]
                record = RUNS.get(run_id)
                if record is None:
                    self._send_error(HTTPStatus.NOT_FOUND, "Run not found")
                    return
                self._send_json(run_to_json(record, include_tail=True))
                return
            self._send_static(parsed.path)
        except Exception as exc:  # pragma: no cover - request guard
            self._send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    def do_POST(self) -> None:  # noqa: N802
        try:
            parsed = urlparse(self.path)
            payload = self._read_json()
            if parsed.path == "/api/preview":
                config = load_dashboard_config()
                command = build_profile_command(
                    str(payload.get("profileId") or ""),
                    payload.get("params") if isinstance(payload.get("params"), dict) else {},
                    config=config,
                )
                self._send_json({"command": command_to_string(command), "argv": command})
                return
            if parsed.path == "/api/runs":
                run = launch_profile(
                    str(payload.get("profileId") or ""),
                    payload.get("params") if isinstance(payload.get("params"), dict) else {},
                )
                self._send_json(run, status=HTTPStatus.CREATED)
                return
            if parsed.path == "/api/config":
                saved = save_dashboard_local_config(payload)
                self._send_json({"saved": str(saved), "config": load_dashboard_config()})
                return
            if parsed.path.startswith("/api/runs/") and parsed.path.endswith("/stop"):
                run_id = parsed.path.strip("/").split("/")[2]
                self._send_json(stop_run(run_id))
                return
            self._send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")
        except KeyError as exc:
            self._send_error(HTTPStatus.NOT_FOUND, f"Unknown id: {exc}")
        except PermissionError as exc:
            self._send_error(HTTPStatus.FORBIDDEN, str(exc))
        except Exception as exc:  # pragma: no cover - request guard
            self._send_error(HTTPStatus.BAD_REQUEST, str(exc))

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _read_json(self) -> JsonMap:
        length = int(self.headers.get("Content-Length") or "0")
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Expected a JSON object")
        return data

    def _send_json(self, data: JsonMap, *, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status: HTTPStatus, message: str) -> None:
        self._send_json({"error": message}, status=status)

    def _send_static(self, request_path: str) -> None:
        static_root = Path(__file__).with_name("static")
        relative = "index.html" if request_path in {"", "/"} else unquote(request_path.lstrip("/"))
        candidate = (static_root / relative).resolve()
        if not str(candidate).startswith(str(static_root.resolve())):
            self._send_error(HTTPStatus.FORBIDDEN, "Invalid static path")
            return
        if not candidate.exists() or not candidate.is_file():
            self._send_error(HTTPStatus.NOT_FOUND, "Static file not found")
            return
        body = candidate.read_bytes()
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK.value)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _make_server(host: str, port: int) -> ThreadingHTTPServer:
    for candidate in range(port, port + 20):
        try:
            return ThreadingHTTPServer((host, candidate), DashboardHandler)
        except OSError:
            continue
    raise OSError(f"No free dashboard port found from {port} to {port + 19}")


def _find_profile(profile_id: str, config: JsonMap | None = None) -> JsonMap:
    for profile in list_profiles(config or load_dashboard_config()):
        if profile["id"] == profile_id:
            return profile
    known = ", ".join(profile["id"] for profile in list_profiles(config))
    raise KeyError(f"{profile_id}. Known profiles: {known}")


def _profile_values(profile: JsonMap, supplied: JsonMap) -> JsonMap:
    values: JsonMap = {}
    for spec in profile.get("params", []):
        if not isinstance(spec, dict):
            continue
        name = str(spec["name"])
        value = supplied.get(name, spec.get("default"))
        param_type = str(spec.get("type") or "text")
        if param_type == "int":
            value = int(value)
            if "min" in spec and value < int(spec["min"]):
                raise ValueError(f"{name} must be >= {spec['min']}")
            if "max" in spec and value > int(spec["max"]):
                raise ValueError(f"{name} must be <= {spec['max']}")
        elif param_type == "float":
            value = float(value)
        elif param_type == "select":
            choices = [str(choice) for choice in spec.get("choices", [])]
            value = str(value)
            if choices and value not in choices:
                raise ValueError(f"{name} must be one of: {', '.join(choices)}")
        else:
            value = str(value)
        values[name] = value
    return values


def _public_profile(profile: JsonMap) -> JsonMap:
    public = dict(profile)
    public.pop("template", None)
    public.pop("command", None)
    return public


def _task_to_json(task: Any) -> JsonMap:
    return {
        "id": task.id,
        "title": task.title,
        "robotFamily": task.robot_family,
        "primaryRobot": task.primary_robot,
        "primaryAsset": task.primary_asset,
        "initialGoal": task.initial_goal,
        "milestones": list(task.milestones),
    }


def _robot_to_json(robot: Any) -> JsonMap:
    return {
        "name": robot.name,
        "kind": robot.kind,
        "modelPath": str(robot.model_path),
        "notes": robot.notes,
        "available": robot.model_path.exists(),
    }


def _asset_to_json(asset: Any) -> JsonMap:
    expected = asset.expected_model_path
    return {
        "name": asset.name,
        "track": asset.track,
        "kind": asset.kind,
        "robot": asset.robot,
        "source": asset.source,
        "repoUrl": asset.repo_url,
        "license": asset.license,
        "priority": asset.priority,
        "notes": asset.notes,
        "localRepo": str(asset.local_repo),
        "modelPath": str(expected) if expected else "",
        "available": asset.is_available,
    }


def _safe_list_envs() -> JsonMap:
    try:
        from winros.envs.registry import list_envs

        return {"items": [env.__dict__ for env in list_envs()], "error": ""}
    except Exception as exc:
        return {"items": [], "error": str(exc)}


def _deep_merge(base: JsonMap, extra: JsonMap) -> JsonMap:
    merged = dict(base)
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _powershell_exe() -> str:
    return shutil.which("powershell.exe") or shutil.which("powershell") or "powershell.exe"


def _subprocess_env() -> dict[str, str]:
    env = dict(os.environ)
    src_path = str(project_root() / "src")
    current = env.get("PYTHONPATH")
    env["PYTHONPATH"] = src_path if not current else f"{src_path}{os.pathsep}{current}"
    return env


def _tail_file(path: Path, limit: int = 6000) -> str:
    if not path.exists():
        return ""
    data = path.read_bytes()
    return data[-limit:].decode("utf-8", errors="replace")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
