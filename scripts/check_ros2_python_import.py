from __future__ import annotations

import importlib
import os
from pathlib import Path
import sys


def add_if_exists(path: Path) -> None:
    if path.exists() and hasattr(os, "add_dll_directory"):
        os.add_dll_directory(str(path))


def main() -> int:
    ros_root = Path(os.environ.get("WINROS_ROS2_ROOT", r"C:\pixi_ws\ros2-windows"))
    pixi_root = Path(os.environ.get("WINROS_ROS2_PIXI_ROOT", r"C:\pixi_ws\.pixi\envs\default"))

    add_if_exists(ros_root / "bin")
    opt_root = ros_root / "opt"
    if opt_root.exists():
        for bin_dir in opt_root.glob("**/bin"):
            add_if_exists(bin_dir)
    add_if_exists(pixi_root)
    add_if_exists(pixi_root / "Library" / "bin")

    site_packages = ros_root / "Lib" / "site-packages"
    if site_packages.exists():
        sys.path.insert(0, str(site_packages))

    importlib.import_module("rclpy")
    print("rclpy_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
