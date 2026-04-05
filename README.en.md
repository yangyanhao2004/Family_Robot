# graduation_project2

Family service robot graduation project, split into four modules:

- `Family_Robot_Back_PC`: backend services and WebSocket/message routing
- `Family_Robot_Web_PC`: browser-based control panel
- `Family_Robot_pi`: Raspberry Pi runtime (voice + remote control)
- `Family_Robot_STM32`: embedded firmware layer

## Pi-Side Integration

`Family_Robot_pi` now includes:

- local voice assistant runtime (wake word, STT, routing, TTS)
- remote WebSocket robot client for command + status exchange

Use `Family_Robot_pi/main.py` as the default launcher.

```bash
python main.py --mode all
```
