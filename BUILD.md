# 构建发行版指南

## 1. 获取 ffmpeg

### 方式 A：官网下载（推荐）

1. 打开 https://ffmpeg.org/download.html
2. 点 "Windows" → 选 "Windows builds from gyan.dev"
3. 下载 **ffmpeg-release-essentials.zip**
4. 解压，把 `bin/ffmpeg.exe` 复制到项目根目录（`F:\dev\ASMR-Cleaner\`）

### 方式 B：winget（Win10+/Win11 自带）

```powershell
winget install ffmpeg
```
安装后 ffmpeg 自动加入系统 PATH，无需手动复制。

---

## 2. 构建 .exe

```bash
pip install pyinstaller
pyinstaller build_exe.spec
```

构建成功后，`dist/ASMR-Cleaner.exe` 就是可分发的单文件程序。

## 3. 给别人用

`dist/ASMR-Cleaner.exe` 是自包含的：
- Python 运行时已打包在内
- ffmpeg 已打包在内（如果构建时存在于项目根目录）
- **不需要安装任何东西**，对方下载这个 .exe 就能直接运行

首次启动会在 `%APPDATA%/ASMR-Cleaner/` 下自动创建设置文件。

## 4. 文件大小与分发

构建后 `dist/` 目录包含：

| 文件 | 大小 | 说明 |
|---|---|---|
| `ASMR-Cleaner.exe` | ~243MB | 自包含（Python + numpy + tkinter） |
| `ffmpeg.exe` | ~98MB | 音频编解码（需随 exe 一起分发） |
| `ffprobe.exe` | ~97MB | 元信息读取（需随 exe 一起分发） |

**发给别人**：把这 3 个文件打包成 zip，对方解压后双击 exe 即可。

### 为什么 exe 还是大

当前环境是 Anaconda Python，numpy 依赖 Intel MKL（~150MB）。用标准 Python（pip 装 numpy）构建，exe 可降到 ~60MB。

### 为什么 ffmpeg 不打包进 exe

PyInstaller `--onefile` 每次启动要解压整个包到临时目录。ffmpeg+ffprobe 共 200MB，打进去导致启动慢 3-5 秒。放在外部文件按需加载，秒开。

### 精简方案

| 方案 | 删除 | 总体积 | 支持格式 |
|---|---|---|---|
| 完整版 | — | ~438MB | WAV/FLAC/MP3/AAC/OGG/M4A/WMA |
| 轻量版 | ffprobe.exe | ~340MB | 同上（元信息降级为 pydub 读取） |
| 极简版 | ffmpeg.exe + ffprobe.exe | ~243MB | 仅 WAV |

---

## 5. 给发布版的建议

1. 把 `ASMR-Cleaner.exe` 和 `README.md` 打包成 zip
2. 发布到 GitHub Releases 或网盘
3. 建议附一个"快速开始.txt"：
   ```
   双击 ASMR-Cleaner.exe 运行
   如果 Windows 提示"未知发布者"，点"更多信息"→"仍要运行"
   ```
