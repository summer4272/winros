# VLA Interface

WinROS keeps VLA optional. The base platform exposes a provider interface that
turns language or future vision-language input into a structured dry-run robot
command. The command is not sent directly to hardware.

## CLI

```powershell
python -m winros --list-vla-providers
python -m winros --vla-provider rules --vla-robot "Unitree Go2" --vla-instruction "walk forward slowly"
```

The current `rules` provider is deterministic and lightweight. It is meant for
interface tests, dashboard demos, and future replacement by local or remote VLA
providers.

## Contract

Input:

- instruction text;
- robot name;
- optional image path;
- optional context dictionary.

Output:

- command type, such as `locomotion`, `manipulation`, `mode`, or `noop`;
- target dictionary;
- confidence;
- dry-run flag;
- provider notes.

Before hardware, every VLA command should pass:

- command schema validation;
- robot mode and dry-run gate;
- joint, velocity, and torque limits;
- timeout and watchdog checks;
- operator-visible logging.

This keeps the future `VLA + RL` path clean: VLA proposes a structured intent,
RL or classical control maps it to robot actions, and the robot adapter validates
the final command before publish.
