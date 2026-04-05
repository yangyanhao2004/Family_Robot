# graduation_project2

Family service robot graduation project, organized as four clear subsystems:

- `Family_Robot_Back_PC`: backend services, WebSocket routing, signaling
- `Family_Robot_Web_PC`: web control panel UI
- `Family_Robot_pi`: Raspberry Pi runtime (voice agent + remote control client)
- `Family_Robot_STM32`: low-level embedded hardware firmware

## Current Pi Merge Status

`Family_Robot_pi` now contains both:

- the original Pi WebSocket control/status logic
- the complete local voice-agent stack from `pibot_local_agent-main`

This keeps the top-level structure simple while preserving subsystem boundaries.

## Quick Start

1. Start backend (`Family_Robot_Back_PC`).
2. Start web panel (`Family_Robot_Web_PC`) if remote control UI is needed.
3. On Raspberry Pi, run `Family_Robot_pi/main.py`:

```bash
python main.py --mode all
```

## Notes

- `pibot_local_agent-main` is kept for historical reference during transition.
- New Pi development should target `Family_Robot_pi`.
