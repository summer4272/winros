# Real Robot Integration

Real hardware should be integrated behind adapters, not directly inside simulation or learning code.

## Adapter Requirements

Every adapter must:

- start in dry-run mode;
- publish telemetry even when no command is active;
- reject commands that exceed configured limits;
- implement timeout and heartbeat behavior;
- expose a visible mode: `sim`, `dry_run`, `hardware`;
- log command IDs and outcomes.

## Suggested Bring-Up Order

1. Connect read-only telemetry.
2. Validate robot model and joint names.
3. Run command validation without motors enabled.
4. Enable one low-speed joint or wheel path.
5. Add watchdog and e-stop checks.
6. Add planning and higher-level actions.

## Do Not Commit

- vendor credentials;
- private SDK binaries when license forbids redistribution;
- robot network addresses for a private lab;
- calibration files that identify a private machine unless intended.

