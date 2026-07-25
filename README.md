# ASMR Cleaner

专门处理 ASMR 直播回放的音频工具。切除长段静音死区，自动添加淡入淡出，保持耳语和触发音完好无损。

A specialized audio tool for ASMR live stream recordings. Removes long silence segments with crossfade at splice points, preserving whispers and trigger sounds.

## 功能 Features

- 🔇 精准检测并切除长段静音（默认 >5 秒，阈值 -55dB 可调）
- 🎚️ 拼接点自动交叉淡入淡出（默认 30ms），无咔嗒声
- 📊 处理后生成永久 JSON 日志，完整记录切除详情
- 🖥️ 中文图形界面，所见即所得
- 🌍 中/英双语支持，一键切换
- 💾 无损输出 WAV，绝不降低原始音质
- 📦 单文件 .exe 打包，下载即用

## 安装 Installation

### 从源码运行 Run from Source

```bash
# 安装依赖
pip install pydub numpy

# 安装 ffmpeg（Windows）
# 下载 ffmpeg.exe 放到项目目录或系统 PATH

# 运行
python main.py
```

### 打包为 EXE Build Executable

```bash
pip install pyinstaller
pyinstaller build_exe.spec
```

## 使用方法 Usage

1. 点击 **浏览** 选择音频文件（支持 WAV / MP3 / FLAC / AAC / OGG）
2. 查看自动显示的文件信息（格式、时长、采样率等）
3. 根据需要调整处理参数：
   - **静音阈值**：低于此音量为"静音"（推荐 -60 到 -40 dB）
   - **最小时长**：静音超过此时长才会被切除（推荐 3-5 秒）
   - **淡入淡出**：拼接点的渐变长度（推荐 20-50 毫秒）
4. 点击 **开始处理**
5. 处理完成后点击 **查看日志** 查看切除详情

## 输出 Output

- 处理后的音频：`原文件名_cleaned.wav`（与输入同目录）
- 处理日志：`原文件名_cleaned_YYYYMMDD_HHMMSS.json`
- 日志包含：原始时长、切除段数、每段的起止时间和时长

## 技术栈 Tech Stack

- Python 3.7+
- pydub (ffmpeg backend)
- numpy
- tkinter (GUI)

## 许可 License

MIT
