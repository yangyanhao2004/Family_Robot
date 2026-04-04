# 开发者启动指南

这份文档面向第一次接手 `pibot_local_agent-main` 的开发者，目标不是介绍“理想架构”，而是说明这个项目在当前代码状态下，怎样才能在 Raspberry Pi 4B 上正确启动并稳定运行。

## 1. 项目定位

`pibot_local_agent-main` 是 Family Robot 的边缘侧语音陪伴模块，负责下面这条链路：

1. 本地持续监听唤醒词 `hey_jarvis`
2. 检测到唤醒词后开始录音
3. 用本地 `whisper.cpp` 做语音转文字
4. 进行请求路由
5. 简单问答直接本地回复
6. 时间、天气、新闻、笑话、系统状态走本地工具
7. 复杂对话默认走云端 Moonshot/Kimi
8. 用本地 Piper TTS 播放回复

当前版本是 headless 运行模式，没有 UI，也不会覆盖桌面。

## 2. 当前默认运行模式

当前代码已经针对 Raspberry Pi 4B 做过现实取舍，默认不是“全本地智能体”，而是“云端优先语音代理”：

- 唤醒词、本地录音、本地 STT、本地 TTS 都在树莓派本地执行
- 普通寒暄和简单身份问答会直接本地快速回复
- 时间、天气、新闻、笑话、系统状态使用本地工具
- 复杂开放式对话优先走云端模型
- 本地 Ollama 路由默认关闭

这样做的原因很简单：Pi 4B 8GB 在当前项目里运行本地 LLM 路由时，延迟明显过高，不适合作为默认模式。

## 3. 关键文件

- `orchestrator.py`
  整个语音链路的主入口
- `config.py`
  默认配置定义
- `config/config.json`
  运行时配置覆盖
- `.env`
  API key，本文件不会提交到 Git
- `audio/`
  录音、STT、TTS
- `senses/wake_word_detector.py`
  唤醒词检测
- `brain/router.py`
  请求路由逻辑
- `brain/tools/`
  本地工具实现

## 4. 启动前准备

### 4.1 代码目录

假设项目目录为：

```bash
/home/ip/pibot_local_agent-main
```

启动前先确认：

```bash
cd /home/ip/pibot_local_agent-main
pwd
```

### 4.2 Python 环境

项目本身不强制虚拟环境名字，只要求依赖已经装好。

常见两种方式：

项目外部虚拟环境：

```bash
source ~/robot/bin/activate
```

项目内虚拟环境：

```bash
source venv313/bin/activate
```

### 4.3 `.env` 配置

如果是第一次拉取项目，先创建 `.env`：

```bash
cp .env.example .env
nano .env
```

至少建议配置：

- `MOONSHOT_API_KEY`
  复杂对话默认走云端，需要它
- `OPENWEATHER_API_KEY`
  天气功能需要它
- `NEWSAPI_KEY`
  新闻功能需要它

注意：

- `.env` 不要提交到 Git
- API key 不要写进源码文件

### 4.4 音频和模型文件

需要准备好：

- USB 麦克风
- 扬声器或耳机输出
- Piper 语音模型
- Whisper 模型

当前代码会自动兼容几种常见路径：

Piper：

- `pibot_local_agent-main/piper/voices/`
- `/home/ip/piper/voices/`

Whisper：

- `pibot_local_agent-main/whisper.cpp/models/`
- `/home/ip/whisper.cpp/models/`

当前配置优先使用：

- `ggml-tiny.en-q5_0.bin`

如果树莓派上没有 `tiny`，代码会自动回退到已有的 `base` 模型，不会因为这个直接启动失败。

## 5. 推荐启动方式

在树莓派上执行：

```bash
source ~/robot/bin/activate
cd /home/ip/pibot_local_agent-main
python orchestrator.py
```

如果一切正常，你会看到类似日志：

```text
Initializing Jarvis...
  - Audio manager
  - TTS engine
  - STT engine
  - Ollama client
  - Router
  - Weather tool
  - News tool
  - Cloud client
  - Wake word detector
Initialization complete!
  - Local LLM routing is disabled for Pi 4B fast mode
  - Dialogue will prefer the cloud model
Jarvis is running. Say 'Hey Jarvis' to activate.
```

这几行的含义是：

- 项目启动成功
- 当前运行模式为 Pi 4B 快速模式
- 对话默认走云端，不依赖本地 Ollama

## 6. 正常使用流程

启动后：

1. 对机器人说 `hey jarvis`
2. 等待进入录音
3. 说出一句完整的问题
4. 机器人完成识别、路由、回答和播报

推荐一次只说一句，不要在一次唤醒里说太长、太绕、带上下文依赖的句子。

更适合当前版本的说法：

- `What's your name?`
- `What time is it?`
- `What's the weather in Beijing?`
- `Tell me a joke.`

不适合当前无上下文模式的说法：

- `What's her name?`
- `What was the number?`
- `What did you say just now?`

因为当前实现里每次唤醒后都会清空上下文，这类句子缺少明确参照对象。

## 7. 当前性能预期

在 Raspberry Pi 4B 上，当前大致预期是：

- 唤醒词检测：可用
- 录音阶段：几秒内结束
- STT：通常仍然是整条链路里最慢的一段
- 简单直接回复：明显快于本地 LLM 模式
- 工具类回复：通常比复杂对话更快

当前默认模式下：

- 不需要为了聊天单独运行 `ollama serve`
- 就算本地 Ollama 没启动，也不影响默认对话路径

## 8. 如果以后硬件更强，如何启用本地模型

如果后续改用更强的硬件，想重新尝试本地 LLM 路由：

1. 修改 `config/config.json`
2. 将 `enable_local_llm_routing` 改为 `true`
3. 启动 Ollama

```bash
ollama serve
ollama pull qwen2.5:1.5b
```

然后再启动项目：

```bash
python orchestrator.py
```

注意：

- 这不是 Pi 4B 的默认推荐模式
- 当前代码保留了这条路径，但默认关闭

## 9. 常见问题排查

### 9.1 启动时报 onnxruntime GPU/CUDA 警告

例如：

```text
GPU device discovery failed
Specified provider 'CUDAExecutionProvider' is not in available provider names
```

这类信息在当前树莓派运行里通常只是警告，不是致命错误，可以先忽略。

### 9.2 `401 Unauthorized`

说明云端 API key 不正确，先检查：

```bash
cat .env
```

确认：

- `MOONSHOT_API_KEY` 是否填写正确
- 修改 `.env` 后是否重新启动了项目

### 9.3 语音模型找不到

如果报 `Voice model not found`，先检查：

```bash
ls /home/ip/piper/voices/
ls /home/ip/pibot_local_agent-main/piper/voices/
```

### 9.4 Whisper 模型找不到

检查：

```bash
ls /home/ip/whisper.cpp/models/
ls /home/ip/pibot_local_agent-main/whisper.cpp/models/
```

### 9.5 唤醒词不稳定

优先检查：

- 麦克风质量
- 麦克风距离
- 环境噪声
- `mic_device_name` 是否匹配当前设备
- `wake_word_threshold` 是否过高或过低

### 9.6 听得到启动语音，但不响应问题

先看日志里的计时：

- `[timing] record`
- `[timing] stt`
- `[timing] route`
- `[timing] response`

判断问题是在：

- 录音结束太慢
- STT 太慢
- 路由错误
- 云端接口失败

## 10. 推荐给新人的最小启动流程

如果你是第一次接手项目，只做下面这些步骤即可：

1. 拉取或复制项目到树莓派
2. 激活已经装好依赖的虚拟环境
3. 检查 `.env`
4. 进入项目目录
5. 运行 `python orchestrator.py`
6. 先测试三句：

```text
What's your name?
What time is it?
What's the weather in Beijing?
```

只有这三句都正常后，再继续测试复杂对话。

## 11. 当前结论

对新人最重要的理解是：

- 这个项目现在已经不是“Pi 4B 上的全本地大模型语音助手”
- 它是“Pi 4B 上的云端优先语音边缘代理”
- 本地负责唤醒、录音、STT、TTS 和工具
- 复杂对话默认交给云端
- 本地 LLM 路由保留，但默认关闭

如果你按照这份文档启动，路径就是当前代码最稳定、最符合真实硬件条件的启动方式。
