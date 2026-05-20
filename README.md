# Family Robot

家庭服务机器人毕业设计，包含四个子系统：树莓派实时后端 + Vue 3 控制面板 + Java 数据后端 + STM32 嵌入式固件。

---

## 系统架构

```
浏览器 (Vue 3) ──WebSocket──▶ Python 后端 (Pi :8080) ──WebSocket──▶ STM32 (UART)
    │                              │
    └──HTTP REST──▶ Java 后端 (PC :8090) ──MySQL
```

| 层 | 技术 | 作用 |
|----|------|------|
| **实时层** | Python FastAPI + WebSocket | Web ↔ Pi ↔ STM32 指令/状态/视频流实时转发 |
| **数据层** | Java Spring Boot + JPA | 用户认证、提醒调度、相册存储、命令日志 |

---

## 子系统概览

| 子系统 | 语言 | 端口 | 目录 |
|--------|------|------|------|
| Family_Robot_pi | Python 3 | 8080 | 实时 WebSocket 中继 + MJPEG 视频流 + 语音助手 Jarvis |
| Family_Robot_Web_PC | Vue 3 + TS | 5173 | 方向控制、AI Chat、提醒管理、相册、WebRTC 语音通话 |
| Family_Robot_Back_PC | Java 21 | 8090 | JWT 认证、用户管理、提醒 CRUD + 定时调度、命令统计 |
| Family_Robot_STM32 | C | — | FreeRTOS、直流电机 PWM、舵机控制、编码器速度测量 |

---

## 环境要求

| 组件 | 要求 |
|------|------|
| Java | JDK 21+（后端编译运行） |
| Maven | 3.6+（后端构建） |
| Node.js | 18+（前端开发） |
| Python | 3.10+（Pi 运行时） |
| MySQL | 8.0+（数据库） |
| 树莓派 | Pi 4B / 5（运行语音助手 + 摄像头 + STM32 串口） |

---

## 详细启动步骤

### 第一步：数据库初始化

1. 安装 MySQL 8.0+ 并启动服务
2. 创建数据库：
   ```sql
   CREATE DATABASE IF NOT EXISTS family_robot DEFAULT CHARACTER SET utf8mb4;
   ```
3. 默认连接：`root / 123456`，数据库 `family_robot`（表由 JPA 自动创建）

### 第二步：启动 Java 后端（PC，端口 8090）

```bash
cd Family_Robot_Back_PC
mvn spring-boot:run
```

**可配置环境变量：**

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DB_URL` | `jdbc:mysql://localhost:3306/family_robot?...` | 数据库连接 |
| `DB_USERNAME` | `root` | 数据库用户名 |
| `DB_PASSWORD` | `123456` | 数据库密码 |
| `SERVER_PORT` | `8090` | 服务端口 |
| `JWT_SECRET` | 内置默认值 | JWT 签名密钥（生产环境须修改） |
| `AES_SECRET` | 内置默认值 | 密码加密密钥（生产环境须修改） |
| `PYTHON_BACKEND_URL` | `http://192.168.137.90:8080` | Python 后端地址（用于发送 VOICE 提醒） |
| `SMTP_USERNAME` | 无默认值（必填） | QQ 邮箱地址（用于发送验证码和提醒邮件） |
| `SMTP_PASSWORD` | 无默认值（必填） | QQ 邮箱 SMTP 授权码（**非** QQ 密码） |

> **邮件配置说明**：
> 1. 复制 `application.yml.example` 为 `application.yml`（`application.yml` 已被 git 忽略，不会泄露）
> 2. 登录 QQ 邮箱 → 设置 → 账户 → POP3/SMTP 服务 → 开启并获取授权码
> 3. 将 QQ 邮箱地址和授权码填入 `SMTP_USERNAME` 和 `SMTP_PASSWORD` 环境变量（或直接在 `application.yml` 中修改）
> 4. 如果不配置邮件，注册时的邮箱验证码功能将不可用

**首次启动后**，系统会通过 `data.sql` 自动创建管理员账号：
- 邮箱：`admin@familybot.com`
- 密码：`admin123`

**Admin 管理面板功能**：
- 用户管理：搜索用户（按姓名/邮箱/机器人序列号）、查看明文密码、**删除用户**（级联删除机器人/相册/提醒等全部关联数据）
- 机器人管理：搜索/排序/日期筛选、注册新机器人、**删除机器人**（如已绑定用户则级联删除用户）
- Admin 账号自身不可被删除

### 第三步：启动 Web 前端（PC，端口 5173）

```bash
cd Family_Robot_Web_PC
npm install
npm run dev
```

**配置文件** `Family_Robot_Web_PC/.env.local`：

```env
# Python FastAPI 后端地址（树莓派 IP + 端口 8080）
VITE_BACKEND_HTTP_URL=http://192.168.137.90:8080

# Java Spring Boot 后端地址（本机 + 端口 8090）
VITE_JAVA_API_URL=http://localhost:8090
```

> **注意**：`VITE_BACKEND_HTTP_URL` 必须指向树莓派的实际 IP 地址。`localhost` 只适用于 Python 后端和前端在同一台机器上运行的情况。

### 第四步：启动 Python 运行时（树莓派）

详细配置见 `Family_Robot_pi/README.md`。

**一键安装（首次使用）：**
```bash
cd Family_Robot_pi
chmod +x setup.sh && ./setup.sh
```

**日常启动：**
```bash
cd Family_Robot_pi
source venv/bin/activate
python main.py --mode all
```

**启动模式：**

| 命令 | 说明 |
|------|------|
| `python main.py --mode all` | 启动全部（后端 + 语音助手 + 远程控制） |
| `python main.py --mode voice` | 仅语音助手（本地语音交互） |
| `python main.py --mode remote` | 仅远程控制（后端 + WS 客户端） |

> **注意**：如果 Python 后端和 Java 后端不在树莓派上，需要在 `.env` 中设置 `FAMILY_ROBOT_WS_URL` 指向实际地址。

---

## 启动顺序总结

```
1. MySQL 服务（开机自启）
2. Java 后端（PC，端口 8090）
3. Web 前端（PC，端口 5173）
4. Python 运行时（Pi，端口 8080）  ← 最后启动，依赖其他服务就绪
```

---

## 端口与网络配置

### 端口分配

| 端口 | 所在机器 | 服务 | 协议 |
|------|----------|------|------|
| **8080** | 树莓派 | Python FastAPI 后端 | HTTP + WebSocket |
| **8090** | PC | Java Spring Boot 后端 | HTTP REST |
| **5173** | PC | Vue 3 开发服务器 | HTTP |
| **3306** | PC / 服务器 | MySQL 数据库 | TCP |
| **11434** | 树莓派 | Ollama 本地 LLM（可选） | HTTP |

### 部署场景与 IP 配置

本项目默认假设 **PC 和树莓派在同一局域网**，通过 Wi-Fi 热点或路由器连接。

**典型拓扑：**

```
PC (192.168.137.1) ←──Wi-Fi──→ 树莓派 (192.168.137.90)
    │                                │
    ├─ Java 后端 :8090               ├─ Python 后端 :8080
    ├─ Vue 前端 :5173                ├─ 语音助手 Jarvis
    └─ MySQL :3306                   └─ STM32 (USB-UART)
```

**需要修改 IP 的地方（共 4 处）：**

| 位置 | 配置项 | 说明 |
|------|--------|------|
| `Family_Robot_Web_PC/.env.local` | `VITE_BACKEND_HTTP_URL` | 前端连接 Python 后端，填**树莓派 IP** |
| `Family_Robot_Web_PC/.env.local` | `VITE_JAVA_API_URL` | 前端连接 Java 后端，填**PC IP** |
| `Family_Robot_Back_PC/application.yml` | `PYTHON_BACKEND_URL` | Java 调用 Python（发送 VOICE 提醒），填**树莓派 IP** |
| `Family_Robot_pi/.env` | `JAVA_BACKEND_URL` | Python 调用 Java（存储提醒），填 **PC IP** |

### 场景一：全部在本机开发（无树莓派）

如果 Python 后端也在 PC 上运行（不使用树莓派的摄像头和语音功能）：

```
VITE_BACKEND_HTTP_URL=http://localhost:8080
VITE_JAVA_API_URL=http://localhost:8090
PYTHON_BACKEND_URL=http://localhost:8080
JAVA_BACKEND_URL=http://localhost:8090
```

将所有 IP 都设为 `localhost`。

### 场景二：PC + 树莓派分离部署（标准场景）

PC（192.168.137.1）运行 Java + 前端，树莓派（192.168.137.90）运行 Python：

```
VITE_BACKEND_HTTP_URL=http://192.168.137.90:8080   # 前端 → 树莓派
VITE_JAVA_API_URL=http://192.168.137.1:8090         # 前端 → 本机 Java
PYTHON_BACKEND_URL=http://192.168.137.90:8080       # Java → 树莓派
JAVA_BACKEND_URL=http://192.168.137.1:8090          # 树莓派 → PC
```

> **关键**：`VITE_BACKEND_HTTP_URL` 运行在浏览器中，所以必须填**局域网 IP**（如 `192.168.x.x`），不能填 `localhost`（`localhost` 在浏览器中指向用户本机，而非树莓派）。

### 查看树莓派 IP

在树莓派终端执行：
```bash
hostname -I
```
或
```bash
ip addr show wlan0 | grep "inet "
```

### 防火墙注意事项

- 树莓派端口 **8080** 需要允许来自 PC 的入站连接
- PC 端口 **8090** 需要允许来自树莓派的入站连接（用于 VOICE 提醒回调）
- PC 端口 **5173** 仅在开发时使用，生产构建后前端为静态文件
- 如果使用 Windows 防火墙，首次运行时会弹出允许提示，点击"允许访问"

### 端口冲突检查

启动前确认端口未被占用：

```bash
# 树莓派
lsof -i :8080

# Windows PC
netstat -ano | findstr "8090"
netstat -ano | findstr "5173"
```

---

## 常见问题

### 1. 前端连接不上视频/机器人控制

- 确认 `VITE_BACKEND_HTTP_URL` 指向树莓派的实际 IP 地址
- 确认树莓派上 `python main.py --mode all` 已启动
- 浏览器 F12 → Console 查看 WebSocket 连接状态

### 2. 用户注册失败

- 确认 Java 后端正在运行（`http://localhost:8090` 可访问）
- 确认 MySQL 数据库已创建
- 检查注册验证码邮件（QQ 邮箱 SMTP）

### 3. 树莓派语音助手不响应

- 确认麦克风和扬声器已连接
- 确认 whisper.cpp 已编译安装（`which whisper-cpp`）
- 确认 Piper TTS 语音模型已下载（`piper/voices/en_GB-semaine-medium.onnx`）
- 唤醒词是 "Hey Jarvis"

### 4. AI Chat 功能不可用

- 确认 `.env` 中已配置 `MOONSHOT_API_KEY`
- 确认网络可访问 `api.moonshot.cn`

### 5. WebRTC 语音通话无声音

- 确认 `aiortc` 已安装
- 确认树莓派 USB 麦克风和耳机已连接
- 查看 Python 日志确认音频设备自动检测结果
