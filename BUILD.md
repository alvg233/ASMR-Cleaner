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

## 4. 文件大小

打包后约 **60-80 MB**（Python runtime ~30MB + ffmpeg ~30MB + 项目代码 ~1MB）。

如果嫌大，可以考虑：
- 去掉 ffmpeg（只支持 WAV，体积减半 ~30MB）
- 使用 UPX 压缩（spec 中 `upx=True` 已启用）

---

## 5. 给发布版的建议

1. 把 `ASMR-Cleaner.exe` 和 `README.md` 打包成 zip
2. 发布到 GitHub Releases 或网盘
3. 建议附一个"快速开始.txt"：
   ```
   双击 ASMR-Cleaner.exe 运行
   如果 Windows 提示"未知发布者"，点"更多信息"→"仍要运行"
   ```
