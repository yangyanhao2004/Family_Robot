# Family Robot

家庭服务机器人毕业设计，包含四个子系统：

- **Family_Robot_pi** — 树莓派统一运行时（FastAPI 后端 + 语音助手 Jarvis + 远程控制客户端）
- **Family_Robot_Web_PC** — Vue 3 浏览器控制面板
- **Family_Robot_Back_PC** — Java Spring Boot 数据后端（用户/提醒/相册）
- **Family_Robot_STM32** — STM32F407 嵌入式固件（FreeRTOS + 电机/舵机控制）

## 架构

```
浏览器 (Vue 3) ──WebSocket──▶ Python 后端 (Pi:8080) ──WebSocket──▶ STM32 (UART)
                    │
                    └──HTTP──▶ Java 后端 (PC:8090) ──MySQL
```

- **实时层**：Python FastAPI 在 Pi 上转发 Web ↔ Pi ↔ STM32 的指令/状态/视频流
- **数据层**：Java Spring Boot 在 PC 上处理认证、提醒、相册等持久化数据

## 快速启动

1. 启动 Java 后端：
   ```bash
   cd Family_Robot_Back_PC
   mvn spring-boot:run
   ```

2. 启动 Web 前端：
   ```bash
   cd Family_Robot_Web_PC
   npm run dev
   ```

3. 在树莓派上启动统一运行时：
   ```bash
   cd Family_Robot_pi
   source venv/bin/activate
   python main.py --mode all
   ```

4. 浏览器访问 `http://<pi-ip>:5173`（开发模式）或构建后的静态页面

## 子系统

| 子系统 | 语言 | 端口 | 说明 |
|--------|------|------|------|
| Family_Robot_pi | Python 3 | 8080 | 实时 WebSocket 中继 + MJPEG 视频流 + 语音助手 |
| Family_Robot_Web_PC | Vue 3 + TS | 5173 | 方向控制、AI Chat、提醒管理、相册、WebRTC 通话 |
| Family_Robot_Back_PC | Java 21 | 8090 | JWT 认证、用户管理、提醒调度、命令日志 |
| Family_Robot_STM32 | C | — | FreeRTOS、直流电机 PWM、舵机、编码器测速 |

详细配置见各子系统目录下的 README。
