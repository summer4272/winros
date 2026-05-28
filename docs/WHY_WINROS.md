# Project Motivation

WinROS is a Windows-first robotics learning platform. It is intended to provide
a practical entry point for users who want to experiment with ROS 2, MuJoCo,
reinforcement learning, VLA-style command generation, and hardware-adapter
interfaces without starting from a full Linux workstation setup.

The project does not replace Linux-based robotics development. Instead, it
offers a smaller first step: run local simulations, inspect trained-policy
previews, test structured command interfaces, and build ROS 2 packages from a
single repository.

## Design Goals

| Goal | Implementation direction |
| --- | --- |
| Lower first-run friction | Windows setup scripts, local dashboard, and small simulation tasks |
| Keep robot-learning workflows connected | Shared configuration for CLI, dashboard, simulation, RL, VLA, and ROS 2 |
| Make demos reproducible | Recording scripts, demo manifest, validation notes, and release checks |
| Keep hardware work safe | Dry-run-first adapters, command validation, telemetry, and explicit hardware gates |
| Keep the public repository clean | No private checkpoints, SDKs, datasets, credentials, or calibration files |

## Current Evidence

The repository currently includes:

- a local dashboard for environment checks, simulations, RL profiles, VLA
  dry-run, and ROS 2 build profiles;
- trained-policy demo previews for Unitree G1 and Unitree Go2 locomotion tasks;
- scripts for recording and rebuilding the public demo assets;
- ROS 2 interface, MuJoCo bridge, and robot-adapter package skeletons;
- a VLA provider interface that returns structured robot commands;
- a lightweight test suite for registry, configuration, and public interfaces.

## Non-Goals

- Distributing private training checkpoints.
- Shipping vendor SDKs or private robot configuration.
- Enabling real hardware control by default.
- Guaranteeing that all research demos can be retrained on low-end hardware.
- Presenting Windows as a replacement for production Linux robot stacks.

## Intended Contribution Areas

- Windows setup reports and dependency fixes.
- Dashboard profiles and UI improvements.
- Small simulation tasks and reproducible RL baselines.
- VLA providers that emit structured dry-run commands.
- ROS 2 message, service, action, and bridge improvements.
- Hardware adapters that remain dry-run by default and document safety limits.
