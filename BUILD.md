# 构建发行版指南

## 1. 获取 ffmpeg

### 方式 A：官网下载（推荐）

1. 打开 https://ffmpeg.org/download.html
2. 点 "Windows" → "Windows builds from gyan.dev"
3. 下载 **ffmpeg-release-essentials.zip**
4. 解压，把 `bin/ffmpeg.exe` 和 `bin/ffprobe.exe` 复制到项目根目录

### 方式 B：winget（Win10+/Win11 自带）

```powershell
winget install ffmpeg
```

## 2. 构建

### 单文件模式（推荐分发）

```bash
.venv/Scripts/python -m PyInstaller build_exe.spec
```

输出：`dist/ASMR-Cleaner.exe`（22MB）

启动时需要解压到临时目录（22MB 解压极快，几乎无感）。

### 文件夹模式（秒启动，开发调试用）

```bash
.venv/Scripts/python -m PyInstaller build_onedir.spec
```

输出：`dist/ASMR-Cleaner/` 文件夹（~248MB 含 ffmpeg）

零解压，瞬间启动。

## 3. 分发

把以下内容打包成 zip 发给别人：

```
ASMR-Cleaner.exe  (22MB)
ffmpeg.exe        (98MB)
ffprobe.exe       (97MB)
README.md
```

对方解压后双击 `ASMR-Cleaner.exe` 即可，**不需要安装 Python、ffmpeg 或任何运行环境**。

首次启动会在 `%APPDATA%/ASMR-Cleaner/` 下自动创建设置文件。

## 4. 文件大小

| 组件 | 大小 | 说明 |
|---|---|---|
| ASMR-Cleaner.exe | 22MB | Python + numpy + tkinter + pydub |
| ffmpeg.exe | 98MB | 音频编解码 |
| ffprobe.exe | 97MB | 元信息读取 |
| **zip 合计** | **~217MB** | — |

### 为什么这么小

关键是**别用 Anaconda Python 构建**。Anaconda 的 numpy 捆绑 Intel MKL 数学库（~500MB），pip 版 numpy 用 OpenBLAS（~30MB）。项目自带 `.venv` 已经是 pip 环境，直接用即可。

### 极简版（仅 WAV）

删掉 ffmpeg.exe 和 ffprobe.exe，exe 只有 22MB，但仅支持 WAV 格式。
