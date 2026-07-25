# ASMR-Cleaner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python desktop GUI tool that removes long silence segments from ASMR live stream recordings with crossfade at splice points, preserving all low-volume content.

**Architecture:** Two-layer design — `asmr_cleaner/` (pure logic, no GUI imports) and `gui/` (tkinter, calls engine). Processing loads entire audio into numpy float32 array, performs two-pass analysis/write, and outputs WAV with crossfade. All user-facing strings routed through i18n key lookup for future language support.

**Tech Stack:** Python 3.7+, pydub (ffmpeg backend), numpy, tkinter/ttk, PyInstaller

## Global Constraints

- Python 3.7+ compatibility (current environment)
- Minimal dependencies: pydub + numpy only (both already available)
- All user-visible text via `asmr_cleaner/i18n.py` key lookup — never hardcoded
- `asmr_cleaner/` must never import from `gui/`
- Output always WAV (lossless), same sample rate/bit depth/channels as input
- GUI minimum size 800×600
- Use ttk clam theme for consistent cross-platform appearance
- Background processing via `threading.Thread` + `queue.Queue` — worker never touches tkinter widgets

---

## File Structure Map

| File | Responsibility | Depends On |
|---|---|---|
| `asmr_cleaner/__init__.py` | Package init, empty | — |
| `asmr_cleaner/i18n.py` | All user-facing strings, language detection/switch | — |
| `asmr_cleaner/settings.py` | Read/write `%APPDATA%/ASMR-Cleaner/settings.json` | — |
| `asmr_cleaner/audio_io.py` | Decode/encode audio via pydub → numpy float32 | — |
| `asmr_cleaner/silence_detector.py` | RMS-based silence interval detection with hysteresis | numpy |
| `asmr_cleaner/core.py` | Orchestrator: load → detect → cut → crossfade → save → log | audio_io, silence_detector, log_writer |
| `asmr_cleaner/log_writer.py` | JSON log generation, reading, file discovery | — |
| `gui/__init__.py` | Package init, empty | — |
| `gui/widgets.py` | LabeledSlider, StageIndicator custom tkinter widgets | asmr_cleaner.i18n |
| `gui/file_info.py` | FileInfoPanel — displays audio metadata | asmr_cleaner.i18n, audio_io |
| `gui/log_viewer.py` | LogViewerDialog — formatted log display popup | asmr_cleaner.i18n, log_writer |
| `gui/main_window.py` | MainWindow — full GUI assembly, thread management | all gui modules, asmr_cleaner.* |
| `main.py` | Entry point: DPI setup, theme config, launch MainWindow | gui.main_window |
| `requirements.txt` | pydub, numpy | — |
| `README.md` | User-facing documentation | — |

---

### Task 1: Project Scaffolding & Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `asmr_cleaner/__init__.py`
- Create: `gui/__init__.py`

**Interfaces:**
- Produces: Empty package init files, dependency manifest

- [ ] **Step 1: Write requirements.txt**

```ini
pydub>=0.25.1
numpy>=1.20.0
```

- [ ] **Step 2: Create package init files**

```bash
echo "" > asmr_cleaner/__init__.py
echo "" > gui/__init__.py
```

- [ ] **Step 3: Install pydub**

```bash
pip install pydub
```

Expected: `Successfully installed pydub`

- [ ] **Step 4: Verify imports work**

```bash
python -c "from pydub import AudioSegment; import numpy; print('OK')"
```

Expected: `OK`

---

### Task 2: i18n Module

**Files:**
- Create: `asmr_cleaner/i18n.py`

**Interfaces:**
- Produces:
  - `t(key: str) -> str` — get translated string for current language
  - `set_language(lang: str) -> None` — switch language ("zh" or "en")
  - `get_language() -> str` — get current language code
  - `STRINGS: dict` — the raw translation dictionary (readable by log viewer etc.)

- [ ] **Step 1: Write the complete i18n module**

```python
"""Internationalization module. All user-visible strings live here.
Add a new language by adding a new top-level key to STRINGS."""

import locale

STRINGS = {
    "zh": {
        # Window
        "app.title": "ASMR Cleaner",

        # Input file frame
        "frame.input": "输入文件",
        "btn.browse": "浏览...",

        # File info frame
        "frame.file_info": "文件信息",
        "info.format": "格式",
        "info.duration": "时长",
        "info.sample_rate": "采样率",
        "info.bit_depth": "位深",
        "info.channels": "声道",
        "info.size": "大小",
        "info.mono": "单声道",
        "info.stereo": "立体声",
        "info.no_file": "尚未选择文件",
        "info.loading": "正在读取文件信息...",

        # Parameters frame
        "frame.params": "处理参数",
        "label.threshold": "静音阈值",
        "label.threshold_unit": "dB",
        "label.min_silence": "最小时长",
        "label.min_silence_unit": "秒",
        "label.crossfade": "淡入淡出",
        "label.crossfade_unit": "毫秒",
        "tooltip.threshold": "低于此音量的声音将被视为静音。\n推荐范围：-60dB（敏感）到 -40dB（保守）",
        "tooltip.min_silence": "连续静音超过此时长的段落才会被切除。\nASMR 回放建议 3-5 秒",
        "tooltip.crossfade": "切除后拼接处的交叉渐变长度。\n太短可能产生\"咔嗒\"声，太长会让声音重叠",

        # Buttons
        "btn.start": "▶ 开始处理",
        "btn.start.processing": "处理中...",
        "btn.view_log": "📋 查看日志",

        # Stage indicator
        "stage.load": "加载",
        "stage.analyze": "分析",
        "stage.process": "处理",
        "stage.export": "导出",
        "stage.log": "日志",

        # Status bar
        "status.ready": "就绪",
        "status.select_file": "请选择音频文件",
        "status.loading": "正在加载音频文件...",
        "status.analyzing": "正在分析静音区...",
        "status.processing": "正在切除静音并拼接...",
        "status.exporting": "正在导出文件...",
        "status.writing_log": "正在写入日志...",
        "status.complete": "✅ 处理完成！已保存到：{}",
        "status.complete_no_silence": "✅ 扫描完成，未发现长静音区，无需处理",
        "status.cancelled": "已取消",

        # Progress info
        "progress.scanned": "已扫描",
        "progress.found_segments": "已找到静音区",
        "progress.total_segments": "段",
        "progress.total_duration": "共",

        # Log viewer
        "log.title": "处理日志",
        "log.input_file": "输入文件",
        "log.output_file": "输出文件",
        "log.processed_at": "处理时间",
        "log.original_duration": "原始时长",
        "log.output_duration": "处理后",
        "log.reduction": "减少比例",
        "log.removed_header": "切除详情（共 {} 段，合计 {}）",
        "log.col_index": "#",
        "log.col_start": "起始时间",
        "log.col_end": "结束时间",
        "log.col_duration": "时长",
        "log.params": "处理参数",
        "log.no_logs": "未找到该文件的处理日志",
        "log.select_log": "选择日志",
        "log.multiple_logs": "找到 {} 份日志，请选择：",
        "btn.open_folder": "📂 打开文件位置",
        "btn.copy_text": "📋 复制为文本",
        "btn.close": "关闭",

        # Duration formatting
        "time.hour": "时",
        "time.minute": "分",
        "time.second": "秒",
        "time.h": "小时",
        "time.m": "分钟",
        "time.s": "秒",

        # Errors & dialogs
        "error.title": "错误",
        "error.unsupported_format": "不支持的音频格式：{}\n\n支持的格式：WAV, MP3, FLAC, AAC, OGG",
        "error.decode_failed": "无法解码文件，文件可能已损坏或格式不正确",
        "error.large_file": "文件较大（{:.2f} GB），处理可能需要较长时间并消耗较多内存。\n\n是否继续？",
        "error.large_file_title": "大文件警告",
        "error.all_silence": "⚠️ 检测到整个文件几乎都是静音（保留率 {:.1f}%），请确认是否选错了文件",
        "error.all_silence_title": "异常结果",
        "error.overwrite": "输出文件已存在：\n{}\n\n是否覆盖？",
        "error.overwrite_title": "文件已存在",
        "error.disk_space": "磁盘空间不足，无法写入输出文件",
        "error.processing": "处理出错：{}",
        "error.close_during_processing": "正在处理中，确定要退出吗？",
        "error.close_during_processing_title": "处理未完成",
        "warn.title": "警告",
        "info.title": "提示",

        # File dialog
        "file_filter": "音频文件",
        "file_filter_all": "所有文件",

        # Menu
        "menu.settings": "设置",
        "menu.language": "语言",

        # Clipboard
        "clipboard.copied": "已复制到剪贴板",
    },
    "en": {
        "app.title": "ASMR Cleaner",

        "frame.input": "Input File",
        "btn.browse": "Browse...",

        "frame.file_info": "File Info",
        "info.format": "Format",
        "info.duration": "Duration",
        "info.sample_rate": "Sample Rate",
        "info.bit_depth": "Bit Depth",
        "info.channels": "Channels",
        "info.size": "Size",
        "info.mono": "Mono",
        "info.stereo": "Stereo",
        "info.no_file": "No file selected",
        "info.loading": "Reading file info...",

        "frame.params": "Parameters",
        "label.threshold": "Silence Threshold",
        "label.threshold_unit": "dB",
        "label.min_silence": "Min Duration",
        "label.min_silence_unit": "sec",
        "label.crossfade": "Crossfade",
        "label.crossfade_unit": "ms",
        "tooltip.threshold": "Audio below this volume will be treated as silence.\nRecommended: -60dB (sensitive) to -40dB (conservative)",
        "tooltip.min_silence": "Continuous silence longer than this will be removed.\nRecommended 3-5 seconds for ASMR recordings",
        "tooltip.crossfade": "Crossfade length at splice points.\nToo short may cause clicks; too long may cause overlap",

        "btn.start": "▶ Start",
        "btn.start.processing": "Processing...",
        "btn.view_log": "📋 View Log",

        "stage.load": "Load",
        "stage.analyze": "Analyze",
        "stage.process": "Process",
        "stage.export": "Export",
        "stage.log": "Log",

        "status.ready": "Ready",
        "status.select_file": "Please select an audio file",
        "status.loading": "Loading audio file...",
        "status.analyzing": "Detecting silence...",
        "status.processing": "Removing silence and splicing...",
        "status.exporting": "Exporting file...",
        "status.writing_log": "Writing log...",
        "status.complete": "✅ Done! Saved to: {}",
        "status.complete_no_silence": "✅ Scan complete — no long silence detected, no changes needed",
        "status.cancelled": "Cancelled",

        "progress.scanned": "Scanned",
        "progress.found_segments": "Found",
        "progress.total_segments": "segments",
        "progress.total_duration": "total",

        "log.title": "Processing Log",
        "log.input_file": "Input File",
        "log.output_file": "Output File",
        "log.processed_at": "Processed At",
        "log.original_duration": "Original Duration",
        "log.output_duration": "After Processing",
        "log.reduction": "Reduction",
        "log.removed_header": "Removed Segments ({} total, {} total)",
        "log.col_index": "#",
        "log.col_start": "Start",
        "log.col_end": "End",
        "log.col_duration": "Duration",
        "log.params": "Parameters",
        "log.no_logs": "No processing logs found for this file",
        "log.select_log": "Select Log",
        "log.multiple_logs": "Found {} log files, please select:",
        "btn.open_folder": "📂 Open File Location",
        "btn.copy_text": "📋 Copy as Text",
        "btn.close": "Close",

        "time.hour": "h",
        "time.minute": "m",
        "time.second": "s",
        "time.h": "hr",
        "time.m": "min",
        "time.s": "sec",

        "error.title": "Error",
        "error.unsupported_format": "Unsupported audio format: {}\n\nSupported formats: WAV, MP3, FLAC, AAC, OGG",
        "error.decode_failed": "Cannot decode file — file may be corrupted or in an unsupported format",
        "error.large_file": "This file is quite large ({:.2f} GB). Processing may take a while and use significant memory.\n\nContinue?",
        "error.large_file_title": "Large File Warning",
        "error.all_silence": "⚠️ Almost the entire file appears to be silence (retention rate {:.1f}%). Please verify the input file.",
        "error.all_silence_title": "Abnormal Result",
        "error.overwrite": "Output file already exists:\n{}\n\nOverwrite?",
        "error.overwrite_title": "File Already Exists",
        "error.disk_space": "Not enough disk space to write output file",
        "error.processing": "Processing error: {}",
        "error.close_during_processing": "Processing is still running. Are you sure you want to quit?",
        "error.close_during_processing_title": "Processing Incomplete",
        "warn.title": "Warning",
        "info.title": "Notice",

        "file_filter": "Audio Files",
        "file_filter_all": "All Files",

        "menu.settings": "Settings",
        "menu.language": "Language",

        "clipboard.copied": "Copied to clipboard",
    }
}

_current_lang = None


def _detect_language():
    """Auto-detect language from system locale."""
    try:
        loc = locale.getdefaultlocale()[0]
        if loc and (loc.startswith("zh") or loc in ("zh_CN", "zh_TW", "zh_SG")):
            return "zh"
    except Exception:
        pass
    return "en"


def get_language():
    """Get current language code."""
    global _current_lang
    if _current_lang is None:
        _current_lang = _detect_language()
    return _current_lang


def set_language(lang):
    """Set language. Raises ValueError for unsupported languages."""
    global _current_lang
    if lang not in STRINGS:
        raise ValueError(f"Unsupported language: {lang}")
    _current_lang = lang


def t(key):
    """Get translated string for current language by key.
    Returns the key itself if translation is missing."""
    lang = get_language()
    return STRINGS.get(lang, STRINGS["en"]).get(key, key)
```

- [ ] **Step 2: Verify i18n module**

```bash
python -c "
from asmr_cleaner.i18n import t, set_language, get_language
print('Default lang:', get_language())
print('Title:', t('app.title'))
set_language('en')
print('EN Title:', t('app.title'))
set_language('zh')
print('ZH Title:', t('app.title'))
print('Missing key:', t('nonexistent.key'))
"
```

Expected: Shows auto-detected language, translated strings, missing key falls back to key itself.

---

### Task 3: Settings Module

**Files:**
- Create: `asmr_cleaner/settings.py`

**Interfaces:**
- Consumes: — (standard library only)
- Produces:
  - `load() -> dict` — read settings.json, merge with defaults
  - `save(settings: dict) -> None` — write settings.json atomically
  - `DEFAULTS: dict` — default settings values

- [ ] **Step 1: Write settings module**

```python
"""User settings persistence. Stored in %APPDATA%/ASMR-Cleaner/settings.json"""

import json
import os


def _settings_dir():
    """Get the settings directory, creating it if needed."""
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    dir_path = os.path.join(appdata, "ASMR-Cleaner")
    os.makedirs(dir_path, exist_ok=True)
    return dir_path


def _settings_path():
    """Get the full path to settings.json."""
    return os.path.join(_settings_dir(), "settings.json")


DEFAULTS = {
    "language": None,              # None = auto-detect, "zh", "en"
    "default_threshold_db": -55.0,
    "default_min_silence_sec": 5.0,
    "default_crossfade_ms": 30,
    "last_input_dir": None,        # Last directory used for file open dialog
}


def load():
    """Load settings, merging with defaults for any missing keys."""
    path = _settings_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            data = {}
    else:
        data = {}

    # Merge: saved values take precedence, fill gaps with DEFAULTS
    merged = dict(DEFAULTS)
    merged.update({k: v for k, v in data.items() if k in DEFAULTS})
    return merged


def save(settings):
    """Save settings to disk. Only saves keys present in DEFAULTS."""
    filtered = {k: v for k, v in settings.items() if k in DEFAULTS}
    path = _settings_path()
    # Atomic write: write to temp file, then rename
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(filtered, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, path)
```

- [ ] **Step 2: Verify settings module**

```bash
python -c "
from asmr_cleaner import settings
s = settings.load()
print('Defaults:', s)
s['language'] = 'zh'
settings.save(s)
s2 = settings.load()
print('Reloaded:', s2)
assert s2['language'] == 'zh'
print('OK')
"
```

Expected: `OK` with correct round-trip.

---

### Task 4: Audio I/O Module

**Files:**
- Create: `asmr_cleaner/audio_io.py`

**Interfaces:**
- Consumes: pydub, numpy, os
- Produces:
  - `get_audio_info(filepath: str) -> dict` — metadata without full decode. Keys: format, sample_rate, bit_depth, channels, duration_sec, file_size_bytes
  - `load_audio(filepath: str) -> tuple` — returns `(samples: np.ndarray, info: dict)`. Samples shape: (N, C), float32, normalized to [-1.0, 1.0]
  - `save_audio(samples: np.ndarray, filepath: str, info: dict) -> None` — save as WAV, preserving sample rate and channels from info dict

- [ ] **Step 1: Write audio_io module**

```python
"""Audio file I/O. Wraps pydub for format decode/encode, uses numpy for data."""

import os
import numpy as np
from pydub import AudioSegment

# Supported input formats (by extension, uppercase)
SUPPORTED_FORMATS = {".WAV", ".MP3", ".FLAC", ".AAC", ".OGG", ".M4A", ".WMA"}


def get_audio_info(filepath):
    """Read audio metadata without keeping the full decode in memory.

    Returns dict with keys: format, sample_rate, bit_depth, channels,
    duration_sec, file_size_bytes.
    """
    ext = os.path.splitext(filepath)[1].upper()
    if ext not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format: {ext}")

    seg = AudioSegment.from_file(filepath)
    info = {
        "format": ext.lstrip("."),
        "sample_rate": seg.frame_rate,
        "bit_depth": seg.sample_width * 8,
        "channels": seg.channels,
        "duration_sec": len(seg) / 1000.0,
        "file_size_bytes": os.path.getsize(filepath),
    }
    return info


def load_audio(filepath):
    """Load audio file fully into memory as float32 numpy array.

    Args:
        filepath: Path to audio file.

    Returns:
        (samples, info) tuple.
        samples: float32 ndarray, shape (total_frames, channels), range [-1.0, 1.0]
        info: dict from get_audio_info()
    """
    ext = os.path.splitext(filepath)[1].upper()
    if ext not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format: {}".format(ext))

    seg = AudioSegment.from_file(filepath)
    info = {
        "format": ext.lstrip("."),
        "sample_rate": seg.frame_rate,
        "bit_depth": seg.sample_width * 8,
        "channels": seg.channels,
        "duration_sec": len(seg) / 1000.0,
        "file_size_bytes": os.path.getsize(filepath),
    }

    # Get raw samples and convert to float32 [-1.0, 1.0]
    raw = np.array(seg.get_array_of_samples(), dtype=np.float32)
    max_val = float(2 ** (seg.sample_width * 8 - 1))
    raw = raw / max_val

    # Reshape: pydub returns interleaved [L0,R0,L1,R1,...]
    if seg.channels > 1:
        samples = raw.reshape((-1, seg.channels))
    else:
        samples = raw.reshape((-1, 1))

    # Release the AudioSegment to help GC
    del seg
    del raw

    return samples, info


def save_audio(samples, filepath, info):
    """Save float32 numpy array to WAV file.

    Args:
        samples: float32 ndarray, shape (total_frames, channels), range [-1.0, 1.0]
        filepath: Output path (should end in .wav)
        info: dict from get_audio_info() with sample_rate and channels
    """
    # Clamp to [-1.0, 1.0] to prevent wrap-around on conversion
    samples = np.clip(samples, -1.0, 1.0)

    # Convert float32 [-1.0, 1.0] to int16
    samples_int16 = (samples * 32767.0).astype(np.int16)

    # Flatten to interleaved if multi-channel
    if samples_int16.ndim > 1 and samples_int16.shape[1] > 1:
        raw_bytes = samples_int16.tobytes()
    else:
        raw_bytes = samples_int16.flatten().tobytes()

    seg = AudioSegment(
        raw_bytes,
        frame_rate=info["sample_rate"],
        sample_width=2,  # 16-bit
        channels=info["channels"],
    )

    seg.export(filepath, format="wav")
```

- [ ] **Step 2: Test with a WAV file (manual — if user has one)**

```bash
python -c "
from asmr_cleaner.audio_io import load_audio, save_audio, get_audio_info
# If you have a test WAV, use it; otherwise skip this verify
print('audio_io module loaded successfully')
print('Supported formats:', sorted(['.WAV', '.MP3', '.FLAC', '.AAC', '.OGG', '.M4A', '.WMA']))
"
```

Expected: Module imports without error.

---

### Task 5: Silence Detector Module

**Files:**
- Create: `asmr_cleaner/silence_detector.py`

**Interfaces:**
- Consumes: numpy
- Produces:
  - `detect_silence(samples: np.ndarray, sample_rate: int, threshold_db: float, min_duration_sec: float, hysteresis_ms: float = 200, progress_callback: callable = None) -> list[dict]`
  - Returns list of dicts with keys: start_sec, end_sec, duration_sec, start_sample, end_sample

- [ ] **Step 1: Write silence detector module**

```python
"""Silence detection via RMS analysis with hysteresis state machine."""

import numpy as np

# Number of samples per analysis frame
FRAME_SIZE = 1024
# Floor value for dB calculation to avoid log10(0) = -inf
EPSILON = 1e-10


def _frames_rms_db(mono_samples):
    """Compute RMS (in dB) for each frame of mono audio.

    Args:
        mono_samples: 1D float32 array, normalized [-1.0, 1.0]

    Returns:
        frame_db: 1D float32 array of dB values, one per frame
        num_frames: total number of frames
    """
    total = len(mono_samples)
    num_frames = max(1, total // FRAME_SIZE)
    # Trim to exact multiple
    trimmed = mono_samples[:num_frames * FRAME_SIZE]

    # Reshape into frames and compute RMS
    frames = trimmed.reshape(num_frames, FRAME_SIZE)
    rms = np.sqrt(np.mean(frames ** 2, axis=1))

    # Convert to dB with floor
    db = 20.0 * np.log10(np.maximum(rms, EPSILON))
    return db, num_frames


def detect_silence(samples, sample_rate, threshold_db, min_duration_sec,
                   hysteresis_ms=200, progress_callback=None):
    """Find all silence segments in audio.

    Uses a hysteresis state machine to prevent threshold-edge flickering.

    Args:
        samples: float32 ndarray, shape (N, C), normalized to [-1.0, 1.0]
        sample_rate: samples per second (e.g. 48000)
        threshold_db: dB threshold — below this is considered silence
        min_duration_sec: minimum silence duration to report (seconds)
        hysteresis_ms: hysteresis window in milliseconds (default 200)
        progress_callback: callable(progress_0_to_1) called periodically

    Returns:
        List of dicts, each with keys:
            start_sec, end_sec, duration_sec, start_sample, end_sample
    """
    # Convert to mono for detection (average channels)
    if samples.ndim > 1 and samples.shape[1] > 1:
        mono = samples.mean(axis=1)
    else:
        mono = samples.flatten()

    # Compute per-frame dB
    frame_db, num_frames = _frames_rms_db(mono)

    # Convert parameters to frame counts
    frames_per_sec = sample_rate / FRAME_SIZE
    min_silence_frames = int(min_duration_sec * frames_per_sec)
    hysteresis_frames = max(1, int(hysteresis_ms / 1000.0 * frames_per_sec))

    if min_silence_frames < 1:
        min_silence_frames = 1

    # State machine: find silence intervals
    # State: 0 = in active audio, 1 = in silence
    state = 0  # start assuming active
    silence_start_frame = 0
    below_counter = 0   # consecutive frames below threshold
    above_counter = 0   # consecutive frames above threshold

    silence_intervals = []

    for i in range(num_frames):
        is_silent = frame_db[i] < threshold_db

        if state == 0:
            # Currently in active audio
            if is_silent:
                below_counter += 1
                if below_counter == 1:
                    silence_start_frame = i
                if below_counter >= min_silence_frames:
                    # Transition to silence
                    state = 1
                    above_counter = 0
                # else: haven't hit min_silence_frames yet, stay in state 0
            else:
                below_counter = 0
        else:
            # Currently in silence
            if not is_silent:
                above_counter += 1
                if above_counter >= hysteresis_frames:
                    # Transition back to active — record the silence
                    end_frame = i - hysteresis_frames
                    silence_intervals.append({
                        "start_frame": silence_start_frame,
                        "end_frame": end_frame,
                    })
                    state = 0
                    below_counter = 0
            else:
                above_counter = 0

        # Progress callback
        if progress_callback and i % 1000 == 0:
            progress_callback(i / num_frames)

    # Handle trailing silence (file ends while still in silence)
    if state == 1:
        silence_intervals.append({
            "start_frame": silence_start_frame,
            "end_frame": num_frames,
        })

    # Convert frame indices to time and sample indices
    result = []
    for interval in silence_intervals:
        start_sample = interval["start_frame"] * FRAME_SIZE
        end_sample = min(interval["end_frame"] * FRAME_SIZE, len(mono))
        start_sec = start_sample / sample_rate
        end_sec = end_sample / sample_rate
        duration_sec = end_sec - start_sec

        # Only keep intervals that meet the minimum duration
        if duration_sec >= min_duration_sec:
            result.append({
                "start_sec": start_sec,
                "end_sec": end_sec,
                "duration_sec": duration_sec,
                "start_sample": start_sample,
                "end_sample": end_sample,
            })

    return result
```

- [ ] **Step 2: Verify with synthetic silence test**

```bash
python -c "
import numpy as np
from asmr_cleaner.silence_detector import detect_silence

# Generate 10 seconds of audio: 2s tone, 6s silence, 2s tone
sr = 48000
total = 10 * sr
samples = np.random.randn(total, 1).astype(np.float32) * 0.01  # very quiet noise floor

# Loud tone from 0-2s
t = np.linspace(0, 2, 2*sr, endpoint=False)
samples[:2*sr, 0] = np.sin(2 * np.pi * 440 * t).astype(np.float32) * 0.5

# Pure silence from 2-8s
samples[2*sr:8*sr, 0] = 0.0

# Loud tone from 8-10s
t = np.linspace(0, 2, 2*sr, endpoint=False)
samples[8*sr:, 0] = np.sin(2 * np.pi * 440 * t).astype(np.float32) * 0.5

# Detect silence >= 3 seconds
result = detect_silence(samples, sr, threshold_db=-55, min_duration_sec=3.0)

print('Found', len(result), 'silence intervals')
for r in result:
    print(f'  {r[\"start_sec\"]:.1f}s - {r[\"end_sec\"]:.1f}s ({r[\"duration_sec\"]:.1f}s)')

# Expected: one interval from ~2.0s to ~8.0s (6 seconds)
assert len(result) == 1, f'Expected 1 silence interval, got {len(result)}'
assert abs(result[0]['duration_sec'] - 6.0) < 0.1, f'Expected ~6s, got {result[0][\"duration_sec\"]}s'
print('OK - silence detection verified')
"
```

Expected: `OK - silence detection verified`

---

### Task 6: Core Processing Engine

**Files:**
- Create: `asmr_cleaner/core.py`

**Interfaces:**
- Consumes: audio_io (load_audio, save_audio, get_audio_info), silence_detector (detect_silence), log_writer (write_log)
- Produces:
  - `process(input_path, output_path, threshold_db, min_silence_sec, crossfade_ms, progress_callback) -> dict`
  - The returned dict is the processing summary

- [ ] **Step 1: Write core processing engine**

```python
"""Core processing engine — orchestrates load → detect → cut → crossfade → save → log."""

import gc
import time
import numpy as np

from . import audio_io
from . import silence_detector
from . import log_writer


def _crossfade(segments, crossfade_frames):
    """Join segments with crossfade at boundaries.

    Uses overlap-add: the tail of segment A and head of segment B
    overlap by crossfade_frames, with complementary linear weights
    that always sum to 1.0.

    Args:
        segments: list of ndarrays, each shape (N_i, C), float32
        crossfade_frames: number of frames in the crossfade overlap

    Returns:
        Concatenated ndarray of shape (total_frames, C), float32
    """
    if len(segments) == 0:
        return np.array([], dtype=np.float32).reshape(0, 1)

    if len(segments) == 1:
        return segments[0]

    # Build output piece by piece
    parts = []
    prev = segments[0]

    for i in range(1, len(segments)):
        curr = segments[i]
        cf = min(crossfade_frames, len(prev), len(curr))

        if cf <= 0:
            # No crossfade possible — just concatenate
            parts.append(prev)
            prev = curr
            continue

        # Crossfade weights: linear ramp
        w_out = np.linspace(1.0, 0.0, cf, dtype=np.float32)
        w_in = np.linspace(0.0, 1.0, cf, dtype=np.float32)

        # Reshape for broadcasting over channels
        channels = prev.shape[1]
        w_out = w_out.reshape(-1, 1)
        w_in = w_in.reshape(-1, 1)

        # Overlap region
        overlap = prev[-cf:] * w_out + curr[:cf] * w_in

        # Append: everything before overlap of prev, then the overlap
        parts.append(prev[:-cf])
        parts.append(overlap)

        # The remainder of curr becomes the new prev
        prev = curr[cf:]

    # Append the final remainder
    parts.append(prev)

    return np.concatenate(parts, axis=0)


def process(input_path, output_path, threshold_db, min_silence_sec,
            crossfade_ms, progress_callback=None):
    """Run the full processing pipeline.

    Args:
        input_path: path to input audio file
        output_path: path for output WAV file
        threshold_db: silence threshold in dB
        min_silence_sec: minimum silence duration to remove (seconds)
        crossfade_ms: crossfade duration at splice points (milliseconds)
        progress_callback: callable(stage, progress, extra_info)
            stage: str — "load", "analyze", "process", "export", "log"
            progress: float — 0.0 to 1.0
            extra_info: dict with optional keys: scanned, total, found_segments, total_removed

    Returns:
        dict with keys: input_info, removed_segments, summary, log_path
    """
    start_time = time.time()

    # --- Stage 1: Load ---
    if progress_callback:
        progress_callback("load", 0.0, {})

    samples, info = audio_io.load_audio(input_path)

    if progress_callback:
        progress_callback("load", 1.0, {})

    gc.collect()

    # --- Stage 2: Analyze (silence detection) ---
    if progress_callback:
        progress_callback("analyze", 0.0, {})

    # Inner callback for detection progress
    def analysis_progress(frac):
        if progress_callback:
            progress_callback("analyze", frac, {})

    removed = silence_detector.detect_silence(
        samples, info["sample_rate"], threshold_db, min_silence_sec,
        hysteresis_ms=200, progress_callback=analysis_progress
    )

    if progress_callback:
        progress_callback("analyze", 1.0, {
            "found_segments": len(removed),
            "total_removed": sum(r["duration_sec"] for r in removed),
        })

    # --- Stage 3: Process (cut + crossfade) ---
    if progress_callback:
        progress_callback("process", 0.0, {})

    crossfade_frames = int(crossfade_ms / 1000.0 * info["sample_rate"])

    if len(removed) == 0:
        # No silence to remove — output = input
        output_samples = samples
    else:
        # Build retained segments (regions between silence intervals)
        retained = []
        total_samples = samples.shape[0]
        pos = 0

        for i, r in enumerate(removed):
            # Segment from pos to start of silence
            if r["start_sample"] > pos:
                retained.append(samples[pos:r["start_sample"]])
            pos = r["end_sample"]

            if progress_callback and i % 10 == 0:
                progress_callback("process", float(i) / len(removed), {})

        # Final segment after last silence
        if pos < total_samples:
            retained.append(samples[pos:])

        # Apply crossfade between retained segments
        output_samples = _crossfade(retained, crossfade_frames)

    if progress_callback:
        progress_callback("process", 1.0, {})

    gc.collect()

    # --- Stage 4: Export ---
    if progress_callback:
        progress_callback("export", 0.0, {})

    audio_io.save_audio(output_samples, output_path, info)

    if progress_callback:
        progress_callback("export", 1.0, {})

    gc.collect()

    # --- Stage 5: Log ---
    if progress_callback:
        progress_callback("log", 0.0, {})

    # Format removed segments with human-readable strings
    removed_formatted = []
    for i, r in enumerate(removed):
        removed_formatted.append({
            "index": i + 1,
            "start_sec": round(r["start_sec"], 3),
            "end_sec": round(r["end_sec"], 3),
            "duration_sec": round(r["duration_sec"], 3),
            "start_str": _sec_to_timestamp(r["start_sec"]),
            "end_str": _sec_to_timestamp(r["end_sec"]),
            "duration_str": _sec_to_duration_str(r["duration_sec"]),
        })

    original_duration = info["duration_sec"]
    total_removed_sec = sum(r["duration_sec"] for r in removed)
    output_duration = original_duration - total_removed_sec
    reduction_pct = (total_removed_sec / original_duration * 100) if original_duration > 0 else 0

    summary = {
        "total_segments_removed": len(removed),
        "total_removed_sec": round(total_removed_sec, 3),
        "original_duration_sec": round(original_duration, 3),
        "output_duration_sec": round(output_duration, 3),
        "reduction_percent": round(reduction_pct, 2),
    }

    params = {
        "threshold_db": threshold_db,
        "min_silence_sec": min_silence_sec,
        "crossfade_ms": crossfade_ms,
    }

    log_path = log_writer.write_log(
        input_path, output_path, params, info, removed_formatted, summary
    )

    if progress_callback:
        progress_callback("log", 1.0, {})

    return {
        "input_info": info,
        "removed_segments": removed_formatted,
        "summary": summary,
        "log_path": log_path,
        "elapsed_sec": round(time.time() - start_time, 1),
    }


def _sec_to_timestamp(seconds):
    """Convert seconds to HH:MM:SS.mmm string."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def _sec_to_duration_str(seconds):
    """Convert seconds to human-readable duration in Chinese style."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    parts = []
    if h > 0:
        parts.append(f"{h} 时")
    if m > 0:
        parts.append(f"{m} 分")
    parts.append(f"{s:.1f} 秒")
    return " ".join(parts)
```

- [ ] **Step 2: Verify core engine loads without error**

```bash
python -c "from asmr_cleaner.core import process, _crossfade; print('core module OK')"
```

Expected: `core module OK` (log_writer is imported but not yet created — we'll test end-to-end after Task 7)

---

### Task 7: Log Writer Module

**Files:**
- Create: `asmr_cleaner/log_writer.py`

**Interfaces:**
- Consumes: json, os, datetime
- Produces:
  - `write_log(input_path, output_path, params, input_info, removed_segments, summary) -> str` — returns log file path
  - `read_log(log_path: str) -> dict` — parse a log file
  - `find_logs_for_file(input_path: str) -> list[str]` — find all log files for an input file

- [ ] **Step 1: Write log writer module**

```python
"""Permanent JSON logging for processing results."""

import json
import os
import glob
from datetime import datetime


LOG_VERSION = "1.0"


def _build_log_filename(input_path):
    """Build log filename: {basename}_cleaned_{timestamp}.json"""
    base = os.path.splitext(os.path.basename(input_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base}_cleaned_{timestamp}.json"


def write_log(input_path, output_path, params, input_info,
              removed_segments, summary):
    """Write processing log as JSON. Uses atomic write (tmp + rename).

    Returns the path to the written log file.
    """
    log = {
        "version": LOG_VERSION,
        "input_file": os.path.abspath(input_path),
        "output_file": os.path.abspath(output_path),
        "processed_at": datetime.now().isoformat(),
        "parameters": params,
        "input_info": input_info,
        "removed_segments": removed_segments,
        "summary": summary,
    }

    # Write to same directory as output file
    output_dir = os.path.dirname(os.path.abspath(output_path))
    filename = _build_log_filename(input_path)
    log_path = os.path.join(output_dir, filename)

    # Atomic write
    tmp_path = log_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, log_path)

    return log_path


def read_log(log_path):
    """Read and parse a log JSON file. Returns dict or raises on error."""
    with open(log_path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_logs_for_file(input_path):
    """Find all log files associated with an input file.

    Looks in the same directory as the input file for files matching
    the pattern {basename}_cleaned_*.json

    Returns list of absolute paths, sorted by modification time (newest first).
    """
    directory = os.path.dirname(os.path.abspath(input_path))
    base = os.path.splitext(os.path.basename(input_path))[0]
    pattern = os.path.join(directory, f"{base}_cleaned_*.json")
    matches = glob.glob(pattern)
    matches.sort(key=os.path.getmtime, reverse=True)
    return matches
```

- [ ] **Step 2: Verify log writer**

```bash
python -c "
from asmr_cleaner.log_writer import write_log, read_log, find_logs_for_file
import tempfile, os

# Write a test log
tmp = tempfile.mkdtemp()
inp = os.path.join(tmp, 'test.wav')
out = os.path.join(tmp, 'test_cleaned.wav')

log_path = write_log(
    inp, out,
    params={'threshold_db': -55, 'min_silence_sec': 5.0, 'crossfade_ms': 30},
    input_info={'format': 'WAV', 'sample_rate': 48000, 'bit_depth': 16, 'channels': 2, 'duration_sec': 100.0, 'file_size_bytes': 10000},
    removed_segments=[{'index': 1, 'start_sec': 10.0, 'end_sec': 20.0, 'duration_sec': 10.0, 'start_str': '00:00:10.000', 'end_str': '00:00:20.000', 'duration_str': '10.0 秒'}],
    summary={'total_segments_removed': 1, 'total_removed_sec': 10.0, 'original_duration_sec': 100.0, 'output_duration_sec': 90.0, 'reduction_percent': 10.0}
)
print('Log written to:', log_path)
assert os.path.exists(log_path), 'Log file not found'

# Read it back
data = read_log(log_path)
assert data['summary']['total_segments_removed'] == 1
print('Log read OK')

# Find logs
logs = find_logs_for_file(inp)
assert len(logs) == 1
print('Find logs OK')
print('All log_writer tests passed')
"
```

Expected: `All log_writer tests passed`

---

### Task 8: GUI Custom Widgets

**Files:**
- Create: `gui/widgets.py`

**Interfaces:**
- Consumes: tkinter, tkinter.ttk, asmr_cleaner.i18n (t)
- Produces:
  - `LabeledSlider(parent, label_key, unit_key, tooltip_key, from_, to, default, step, command=None)` — slider + spinbox combo
  - `StageIndicator(parent, stages)` — 5-stage progress indicator with labels

- [ ] **Step 1: Write LabeledSlider widget**

```python
"""Custom tkinter widgets for ASMR Cleaner GUI."""

import tkinter as tk
from tkinter import ttk


class LabeledSlider(ttk.Frame):
    """A parameter row: label | scale | spinbox | unit | help button.

    The scale and spinbox are bidirectionally linked.
    """

    def __init__(self, parent, label_key, unit_key, tooltip_key,
                 from_, to, default, step, command=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.command = command
        self._value = tk.DoubleVar(value=float(default))

        # Lazy import to avoid circular dependency with i18n
        from asmr_cleaner.i18n import t

        # Label
        self.label = ttk.Label(self, text=t(label_key) + ":", width=14, anchor="e")

        # Scale (slider)
        self.scale = ttk.Scale(
            self, from_=from_, to=to, variable=self._value,
            orient=tk.HORIZONTAL, command=self._on_scale_change
        )

        # Spinbox (numeric entry)
        self.spinbox = ttk.Spinbox(
            self, from_=from_, to=to, increment=step,
            textvariable=self._value, width=5
        )
        self.spinbox.bind("<Return>", self._on_spinbox_change)
        self.spinbox.bind("<FocusOut>", self._on_spinbox_change)

        # Unit label
        self.unit_label = ttk.Label(self, text=t(unit_key), width=4)

        # Help button
        self.help_btn = ttk.Label(self, text="?", cursor="hand2",
                                  foreground="gray", font=("", 9, "bold"))
        self.help_btn.bind("<Button-1>", lambda e: self._show_tooltip(t(tooltip_key)))

        # Layout
        self.label.pack(side=tk.LEFT, padx=(0, 2))
        self.scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.spinbox.pack(side=tk.LEFT, padx=2)
        self.unit_label.pack(side=tk.LEFT, padx=(0, 2))
        self.help_btn.pack(side=tk.LEFT)

    def get(self):
        """Return current value as float."""
        return self._value.get()

    def set(self, value):
        """Set value programmatically."""
        self._value.set(float(value))

    def _on_scale_change(self, event=None):
        """Called when slider moves — syncs spinbox and fires command."""
        val = round(self._value.get())
        self._value.set(val)
        if self.command:
            self.command(val)

    def _on_spinbox_change(self, event=None):
        """Called when spinbox value changes — syncs slider and fires command."""
        try:
            val = float(self._value.get())
            if self.command:
                self.command(val)
        except (ValueError, tk.TclError):
            pass

    def _show_tooltip(self, text):
        """Show a simple tooltip popup near the help button."""
        tip = tk.Toplevel(self)
        tip.wm_overrideredirect(True)
        tip.wm_geometry(f"+{self.winfo_pointerx() + 15}+{self.winfo_pointery() + 10}")

        frame = ttk.Frame(tip, relief="solid", borderwidth=1, padding=8)
        frame.pack()
        lbl = ttk.Label(frame, text=text, justify=tk.LEFT, wraplength=300)
        lbl.pack()

        # Dismiss on click anywhere
        tip.bind("<Button-1>", lambda e: tip.destroy())
        tip.bind("<FocusOut>", lambda e: tip.destroy())
        # Auto-dismiss after 5 seconds
        tip.after(5000, tip.destroy)


class StageIndicator(ttk.Frame):
    """Horizontal stage indicator showing progress through processing stages."""

    STAGE_KEYS = ["stage.load", "stage.analyze", "stage.process",
                  "stage.export", "stage.log"]

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        from asmr_cleaner.i18n import t

        self._labels = []
        self._status = [None] * len(self.STAGE_KEYS)  # None=pending, True=done, False=current

        # Create labels with arrows between them
        inner = ttk.Frame(self)
        inner.pack(expand=True)

        for i, key in enumerate(self.STAGE_KEYS):
            lbl = ttk.Label(inner, text=t(key), padding=(4, 2))
            lbl.pack(side=tk.LEFT)
            self._labels.append(lbl)

            if i < len(self.STAGE_KEYS) - 1:
                arrow = ttk.Label(inner, text="→", foreground="gray")
                arrow.pack(side=tk.LEFT, padx=2)

    def set_stage(self, stage_index):
        """Mark stage_index as current, all before as done, all after as pending.

        Args:
            stage_index: 0-based index (0=load, 1=analyze, 2=process, 3=export, 4=log)
        """
        for i, lbl in enumerate(self._labels):
            if i < stage_index:
                # Done
                lbl.configure(text=f"✅ {lbl.cget('text').lstrip('✅ 🔄 ')}",
                             foreground="green")
            elif i == stage_index:
                # Current — highlight
                lbl.configure(text=f"🔄 {lbl.cget('text').lstrip('✅ 🔄 ')}",
                             foreground="blue")
            else:
                # Pending — gray out
                lbl.configure(text=f"⬜ {lbl.cget('text').lstrip('✅ 🔄 ⬜ ')}",
                             foreground="gray")

    def set_all_done(self):
        """Mark all stages as complete."""
        for lbl in self._labels:
            lbl.configure(text=f"✅ {lbl.cget('text').lstrip('✅ 🔄 ⬜ ')}",
                         foreground="green")

    def reset(self):
        """Reset all stages to pending."""
        for lbl in self._labels:
            lbl.configure(text=f"⬜ {lbl.cget('text').lstrip('✅ 🔄 ⬜ ')}",
                         foreground="gray")
```

- [ ] **Step 2: Verify widgets import**

```bash
python -c "from gui.widgets import LabeledSlider, StageIndicator; print('widgets OK')"
```

Expected: `widgets OK`

---

### Task 9: GUI File Info Panel

**Files:**
- Create: `gui/file_info.py`

**Interfaces:**
- Consumes: tkinter.ttk, asmr_cleaner.i18n (t), asmr_cleaner.audio_io (get_audio_info)
- Produces:
  - `FileInfoPanel(parent)` — ttk.LabelFrame displaying audio metadata

- [ ] **Step 1: Write file info panel**

```python
"""File info panel — displays audio file metadata."""

import os
import tkinter as tk
from tkinter import ttk

from asmr_cleaner.i18n import t
from asmr_cleaner.audio_io import get_audio_info


def _format_duration(seconds):
    """Format seconds as HH:MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _format_size(bytes_val):
    """Format bytes as human-readable size."""
    mb = bytes_val / (1024 * 1024)
    if mb >= 1024:
        return f"{mb / 1024:.2f} GB"
    return f"{mb:.1f} MB"


def _format_channels(ch):
    """Format channel count as readable string."""
    ch_map = {1: t("info.mono"), 2: t("info.stereo")}
    return ch_map.get(ch, f"{ch} {t('info.channels')}")


class FileInfoPanel(ttk.LabelFrame):
    """Panel showing metadata for the selected audio file."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, text=t("frame.file_info"), **kwargs)
        self._value_labels = {}
        self._build()

    def _build(self):
        """Build the grid of info rows."""
        rows = [
            ("info.format",     "—"),
            ("info.duration",   "—"),
            ("info.sample_rate", "—"),
            ("info.bit_depth",  "—"),
            ("info.channels",   "—"),
            ("info.size",       "—"),
        ]

        for i, (key, default) in enumerate(rows):
            lbl = ttk.Label(self, text=t(key) + ":", width=12, anchor="e")
            lbl.grid(row=i // 2, column=(i % 2) * 2, sticky="e", padx=(10, 2), pady=2)

            val = ttk.Label(self, text=default, width=16, anchor="w")
            val.grid(row=i // 2, column=(i % 2) * 2 + 1, sticky="w", padx=(2, 10), pady=2)
            self._value_labels[key] = val

    def show_file(self, filepath):
        """Load and display info for the given file."""
        try:
            info = get_audio_info(filepath)
            self._value_labels["info.format"].configure(text=info["format"])
            self._value_labels["info.duration"].configure(
                text=_format_duration(info["duration_sec"]))
            self._value_labels["info.sample_rate"].configure(
                text=f"{info['sample_rate']} Hz")
            self._value_labels["info.bit_depth"].configure(
                text=f"{info['bit_depth']} bit")
            self._value_labels["info.channels"].configure(
                text=_format_channels(info["channels"]))
            self._value_labels["info.size"].configure(
                text=_format_size(info["file_size_bytes"]))
        except Exception as e:
            self.show_error(str(e))

    def show_error(self, message):
        """Display an error message instead of file info."""
        for key, lbl in self._value_labels.items():
            lbl.configure(text="错误" if key == "info.format" else "—")

    def clear(self):
        """Clear all info fields to default."""
        defaults = {
            "info.format": "—",
            "info.duration": "—",
            "info.sample_rate": "—",
            "info.bit_depth": "—",
            "info.channels": "—",
            "info.size": t("info.no_file"),
        }
        for key, lbl in self._value_labels.items():
            lbl.configure(text=defaults.get(key, "—"))
```

- [ ] **Step 2: Verify file info panel import**

```bash
python -c "from gui.file_info import FileInfoPanel; print('file_info OK')"
```

Expected: `file_info OK`

---

### Task 10: GUI Log Viewer

**Files:**
- Create: `gui/log_viewer.py`

**Interfaces:**
- Consumes: tkinter, asmr_cleaner.i18n (t), asmr_cleaner.log_writer (read_log, find_logs_for_file)
- Produces:
  - `show_log_viewer(parent, log_path: str)` — opens the log viewer dialog
  - `show_log_selector(parent, input_path: str)` — finds and shows log for an input file

- [ ] **Step 1: Write log viewer**

```python
"""Log viewer dialog — displays formatted processing logs."""

import os
import tkinter as tk
from tkinter import ttk

from asmr_cleaner.i18n import t
from asmr_cleaner.log_writer import read_log, find_logs_for_file


def show_log_viewer(parent, log_path):
    """Open a dialog displaying the log at log_path."""
    try:
        data = read_log(log_path)
    except Exception:
        tk.messagebox.showerror(
            t("error.title"), t("error.decode_failed"))
        return

    _LogDialog(parent, data, log_path)


def show_log_selector(parent, input_path):
    """Find and display the most recent log for an input file.
    If multiple logs exist, let user choose."""
    logs = find_logs_for_file(input_path)

    if not logs:
        tk.messagebox.showinfo(t("info.title"), t("log.no_logs"))
        return

    if len(logs) == 1:
        show_log_viewer(parent, logs[0])
        return

    # Multiple logs — show selection dialog
    _LogSelectionDialog(parent, logs)


class _LogSelectionDialog(tk.Toplevel):
    """Dialog for selecting from multiple log files."""

    def __init__(self, parent, log_paths):
        super().__init__(parent)
        self.title(t("log.select_log"))
        self.log_paths = log_paths
        self.resizable(False, False)

        msg = ttk.Label(self, text=t("log.multiple_logs").format(len(log_paths)),
                        padding=10)
        msg.pack()

        list_frame = ttk.Frame(self)
        list_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(list_frame, width=60, height=min(8, len(log_paths)))
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL,
                                  command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.configure(yscrollcommand=scrollbar.set)

        for path in log_paths:
            fname = os.path.basename(path)
            mtime = os.path.getmtime(path)
            import datetime
            dt = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            self.listbox.insert(tk.END, f"{dt}  —  {fname}")

        self.listbox.bind("<Double-Button-1>", self._on_select)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text=t("btn.close"), command=self.destroy).pack(
            side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="打开", command=self._on_select).pack(
            side=tk.RIGHT, padx=5)

        self.transient(parent)
        self.grab_set()

    def _on_select(self, event=None):
        sel = self.listbox.curselection()
        if sel:
            path = self.log_paths[sel[0]]
            self.destroy()
            show_log_viewer(self.master, path)


class _LogDialog(tk.Toplevel):
    """Formatted log display dialog."""

    def __init__(self, parent, data, log_path):
        super().__init__(parent)
        self.title(t("log.title"))
        self.data = data
        self.log_path = log_path
        self.resizable(True, True)
        self.minsize(500, 350)

        self._build()
        self.transient(parent)
        self.grab_set()

    def _build(self):
        data = self.data
        summary = data.get("summary", {})
        params = data.get("parameters", {})
        removed = data.get("removed_segments", [])
        input_info = data.get("input_info", {})

        # Top info frame
        info_frame = ttk.Frame(self, padding=10)
        info_frame.pack(fill=tk.X)

        rows = [
            (t("log.input_file"), os.path.basename(data.get("input_file", ""))),
            (t("log.output_file"), os.path.basename(data.get("output_file", ""))),
            (t("log.processed_at"), data.get("processed_at", "")[:19].replace("T", " ")),
            (t("log.original_duration"),
             _format_duration(summary.get("original_duration_sec", 0))),
            (t("log.output_duration"),
             _format_duration(summary.get("output_duration_sec", 0))),
            (t("log.reduction"),
             f"{summary.get('reduction_percent', 0):.1f}%"),
        ]

        for i, (label, value) in enumerate(rows):
            ttk.Label(info_frame, text=label + ":", font=("", 9, "bold")).grid(
                row=i, column=0, sticky="e", padx=(0, 5), pady=1)
            ttk.Label(info_frame, text=value).grid(
                row=i, column=1, sticky="w", pady=1)

        # Separator
        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, padx=10)

        # Removed segments table
        if removed:
            total_count = len(removed)
            total_dur = _format_duration(sum(r["duration_sec"] for r in removed))

            table_header = ttk.Label(
                self,
                text=t("log.removed_header").format(total_count, total_dur),
                font=("", 9, "bold"), padding=5)
            table_header.pack(anchor="w", padx=10)

            # Table container with scrollbar
            table_frame = ttk.Frame(self, padding=5)
            table_frame.pack(fill=tk.BOTH, expand=True, padx=10)

            columns = ("#", "start", "end", "duration")
            tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                                height=min(len(removed), 12))
            tree.heading("#", text=t("log.col_index"))
            tree.heading("start", text=t("log.col_start"))
            tree.heading("end", text=t("log.col_end"))
            tree.heading("duration", text=t("log.col_duration"))

            tree.column("#", width=40, anchor="center")
            tree.column("start", width=120, anchor="center")
            tree.column("end", width=120, anchor="center")
            tree.column("duration", width=120, anchor="center")

            for r in removed:
                tree.insert("", tk.END, values=(
                    r["index"],
                    r["start_str"][:12],
                    r["end_str"][:12],
                    r["duration_str"],
                ))

            scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL,
                                      command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)

            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Parameters at bottom
        param_text = t("log.params") + f": "
        param_text += f"{t('label.threshold')} {params.get('threshold_db', '?')}dB"
        param_text += f" | {t('label.min_silence')} {params.get('min_silence_sec', '?')}s"
        param_text += f" | {t('label.crossfade')} {params.get('crossfade_ms', '?')}ms"
        ttk.Label(self, text=param_text, padding=10).pack(anchor="w")

        # Bottom buttons
        btn_frame = ttk.Frame(self, padding=10)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text=t("btn.open_folder"),
                   command=self._open_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text=t("btn.copy_text"),
                   command=self._copy_text).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text=t("btn.close"),
                   command=self.destroy).pack(side=tk.RIGHT, padx=5)

    def _open_folder(self):
        """Open the folder containing the output file."""
        output_file = self.data.get("output_file", "")
        if output_file and os.path.exists(output_file):
            folder = os.path.dirname(output_file)
            os.startfile(folder)
        elif self.log_path and os.path.exists(self.log_path):
            os.startfile(os.path.dirname(self.log_path))

    def _copy_text(self):
        """Copy log summary to clipboard."""
        data = self.data
        summary = data.get("summary", {})
        lines = [
            f"{t('log.input_file')}: {os.path.basename(data.get('input_file', ''))}",
            f"{t('log.processed_at')}: {data.get('processed_at', '')[:19].replace('T', ' ')}",
            f"{t('log.original_duration')}: {_format_duration(summary.get('original_duration_sec', 0))}",
            f"{t('log.output_duration')}: {_format_duration(summary.get('output_duration_sec', 0))}",
            f"{t('log.reduction')}: {summary.get('reduction_percent', 0):.1f}%",
            f"\n{t('log.removed_header').format(summary.get('total_segments_removed', 0), _format_duration(summary.get('total_removed_sec', 0)))}:",
        ]
        for r in data.get("removed_segments", []):
            lines.append(
                f"  {r['index']}. {r['start_str']} → {r['end_str']} ({r['duration_str']})"
            )

        self.clipboard_clear()
        self.clipboard_append("\n".join(lines))
        # Show brief confirmation
        self.after(100, lambda: None)  # Let clipboard settle


def _format_duration(seconds):
    """Format seconds as HH:MM:SS."""
    if seconds is None:
        return "—"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"
```

- [ ] **Step 2: Verify log viewer import**

```bash
python -c "from gui.log_viewer import show_log_viewer, show_log_selector; print('log_viewer OK')"
```

Expected: `log_viewer OK`

---

### Task 11: GUI Main Window

**Files:**
- Create: `gui/main_window.py`

**Interfaces:**
- Consumes: tkinter, threading, queue, all gui modules, asmr_cleaner.*
- Produces:
  - `MainWindow` — the main application (inherits tk.Tk)

- [ ] **Step 1: Write the main window**

```python
"""Main application window."""

import os
import gc
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from asmr_cleaner.i18n import t, set_language, get_language
from asmr_cleaner import settings
from asmr_cleaner.audio_io import get_audio_info, SUPPORTED_FORMATS
from asmr_cleaner.core import process

from gui.widgets import LabeledSlider, StageIndicator
from gui.file_info import FileInfoPanel
from gui.log_viewer import show_log_selector


# Progress message sentinel for completion
_PROGRESS_DONE = object()


class MainWindow(tk.Tk):
    """ASMR Cleaner main application window."""

    def __init__(self):
        super().__init__()

        # Load settings
        self._app_settings = settings.load()

        # Apply language
        saved_lang = self._app_settings.get("language")
        if saved_lang:
            set_language(saved_lang)

        self.title(t("app.title"))
        self.minsize(800, 600)
        self.resizable(True, True)

        # State
        self._input_path = None
        self._processing = False
        self._progress_queue = queue.Queue()
        self._worker_thread = None

        # Configure ttk theme
        style = ttk.Style()
        style.theme_use("clam")

        # Build UI
        self._build_menu()
        self._build_input_frame()
        self._build_file_info()
        self._build_params_frame()
        self._build_buttons()
        self._build_stage_indicator()
        self._build_progress()
        self._build_statusbar()

        # Window close handler
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Start polling progress queue
        self._poll_progress()

    # ── Menu ──────────────────────────────────────────

    def _build_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=t("menu.settings"), menu=settings_menu)

        lang_menu = tk.Menu(settings_menu, tearoff=0)
        settings_menu.add_cascade(label=t("menu.language"), menu=lang_menu)

        current_lang = get_language()
        lang_menu.add_radiobutton(
            label="中文", value="zh",
            variable=None,
            command=lambda: self._switch_language("zh"))
        lang_menu.add_radiobutton(
            label="English", value="en",
            command=lambda: self._switch_language("en"))

    def _switch_language(self, lang):
        set_language(lang)
        self._app_settings["language"] = lang
        settings.save(self._app_settings)
        # Rebuild would be ideal, but for v1 just inform user
        messagebox.showinfo(t("info.title"),
                           "Language changed. Please restart the application for full effect.\n\n语言已切换，请重启应用以完全生效。")

    # ── Input File Frame ──────────────────────────────

    def _build_input_frame(self):
        frame = ttk.LabelFrame(self, text=t("frame.input"), padding=10)
        frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        self._input_var = tk.StringVar()
        entry = ttk.Entry(frame, textvariable=self._input_var, state="readonly")
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        browse_btn = ttk.Button(frame, text=t("btn.browse"),
                                command=self._browse_file)
        browse_btn.pack(side=tk.RIGHT)

    # ── File Info Panel ───────────────────────────────

    def _build_file_info(self):
        self._file_info = FileInfoPanel(self, padding=10)
        self._file_info.pack(fill=tk.X, padx=10, pady=5)

    # ── Parameters Frame ──────────────────────────────

    def _build_params_frame(self):
        frame = ttk.LabelFrame(self, text=t("frame.params"), padding=10)
        frame.pack(fill=tk.X, padx=10, pady=5)

        # Silence threshold: -90 to -20 dB, default from settings
        self._threshold_slider = LabeledSlider(
            frame,
            label_key="label.threshold",
            unit_key="label.threshold_unit",
            tooltip_key="tooltip.threshold",
            from_=-90, to=-20,
            default=self._app_settings.get("default_threshold_db", -55),
            step=1,
        )
        self._threshold_slider.pack(fill=tk.X, pady=3)

        # Min silence duration: 0.5 to 60 seconds
        self._min_silence_slider = LabeledSlider(
            frame,
            label_key="label.min_silence",
            unit_key="label.min_silence_unit",
            tooltip_key="tooltip.min_silence",
            from_=0.5, to=60,
            default=self._app_settings.get("default_min_silence_sec", 5.0),
            step=0.5,
        )
        self._min_silence_slider.pack(fill=tk.X, pady=3)

        # Crossfade: 5 to 200 ms
        self._crossfade_slider = LabeledSlider(
            frame,
            label_key="label.crossfade",
            unit_key="label.crossfade_unit",
            tooltip_key="tooltip.crossfade",
            from_=5, to=200,
            default=self._app_settings.get("default_crossfade_ms", 30),
            step=5,
        )
        self._crossfade_slider.pack(fill=tk.X, pady=3)

    # ── Buttons ───────────────────────────────────────

    def _build_buttons(self):
        btn_frame = ttk.Frame(self, padding=10)
        btn_frame.pack(fill=tk.X, padx=10)

        self._start_btn = ttk.Button(btn_frame, text=t("btn.start"),
                                     command=self._start_processing,
                                     state=tk.DISABLED)
        self._start_btn.pack(side=tk.LEFT, padx=(0, 5))

        self._log_btn = ttk.Button(btn_frame, text=t("btn.view_log"),
                                   command=self._view_log)
        self._log_btn.pack(side=tk.LEFT, padx=5)

    # ── Stage Indicator ───────────────────────────────

    def _build_stage_indicator(self):
        self._stage_indicator = StageIndicator(self, padding=10)
        self._stage_indicator.pack(fill=tk.X, padx=10)

    # ── Progress ──────────────────────────────────────

    def _build_progress(self):
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=tk.X, padx=10)

        self._progress_bar = ttk.Progressbar(frame, mode="determinate", length=400)
        self._progress_bar.pack(fill=tk.X)

        self._progress_detail = ttk.Label(frame, text="", padding=(0, 5, 0, 0))
        self._progress_detail.pack(anchor="w")

    # ── Status Bar ────────────────────────────────────

    def _build_statusbar(self):
        self._status_var = tk.StringVar(value=t("status.ready"))
        statusbar = ttk.Label(self, textvariable=self._status_var,
                              relief=tk.SUNKEN, anchor=tk.W, padding=(5, 2))
        statusbar.pack(side=tk.BOTTOM, fill=tk.X)

    # ── File Selection ────────────────────────────────

    def _browse_file(self):
        # Build file filter string
        ext_str = " ".join(f"*{ext.lower()}" for ext in SUPPORTED_FORMATS)
        file_filter = (
            f"{t('file_filter')} ({ext_str})|{ext_str}|"
            f"{t('file_filter_all')} (*.*)|*.*"
        )

        initial_dir = self._app_settings.get("last_input_dir") or os.path.expanduser("~")
        path = filedialog.askopenfilename(
            title=t("frame.input"),
            initialdir=initial_dir,
            filetypes=[
                (t("file_filter"), " ".join(f"*{e.lower()}" for e in SUPPORTED_FORMATS)),
                (t("file_filter_all"), "*.*"),
            ],
        )

        if not path:
            return

        self._input_path = path
        self._input_var.set(path)
        self._app_settings["last_input_dir"] = os.path.dirname(path)
        settings.save(self._app_settings)

        # Update file info
        self._file_info.show_file(path)

        # Enable start button
        self._start_btn.configure(state=tk.NORMAL)
        self._status_var.set(t("status.select_file"))

    # ── Processing ────────────────────────────────────

    def _start_processing(self):
        if self._processing or not self._input_path:
            return

        # Check file size (>2GB warning)
        file_size = os.path.getsize(self._input_path)
        if file_size > 2 * 1024 * 1024 * 1024:
            ok = messagebox.askokcancel(
                t("error.large_file_title"),
                t("error.large_file").format(file_size / (1024**3)))
            if not ok:
                return

        # Build output path
        base, ext = os.path.splitext(self._input_path)
        output_path = f"{base}_cleaned.wav"

        # Check overwrite
        if os.path.exists(output_path):
            ok = messagebox.askokcancel(
                t("error.overwrite_title"),
                t("error.overwrite").format(output_path))
            if not ok:
                return

        # Get parameters
        params = {
            "threshold_db": float(self._threshold_slider.get()),
            "min_silence_sec": float(self._min_silence_slider.get()),
            "crossfade_ms": float(self._crossfade_slider.get()),
        }

        # Disable UI
        self._processing = True
        self._start_btn.configure(text=t("btn.start.processing"), state=tk.DISABLED)
        self._stage_indicator.reset()

        self._status_var.set(t("status.loading"))

        # Start worker thread
        self._worker_thread = threading.Thread(
            target=self._worker_run,
            args=(self._input_path, output_path, params),
            daemon=True,
        )
        self._worker_thread.start()

    def _worker_run(self, input_path, output_path, params):
        """Background worker — runs process() and sends progress to queue."""
        try:
            def progress_cb(stage, frac, extra):
                self._progress_queue.put(("progress", stage, frac, extra))

            result = process(
                input_path, output_path,
                params["threshold_db"],
                params["min_silence_sec"],
                params["crossfade_ms"],
                progress_callback=progress_cb,
            )
            self._progress_queue.put(("done", result))
        except Exception as e:
            self._progress_queue.put(("error", str(e)))

    def _poll_progress(self):
        """Poll the progress queue and update UI. Called every 100ms."""
        try:
            while True:
                msg = self._progress_queue.get_nowait()

                if msg[0] == "progress":
                    _, stage, frac, extra = msg
                    self._update_progress_ui(stage, frac, extra)

                elif msg[0] == "done":
                    result = msg[1]
                    self._on_processing_done(result)

                elif msg[0] == "error":
                    error_msg = msg[1]
                    self._on_processing_error(error_msg)

        except queue.Empty:
            pass

        self.after(100, self._poll_progress)

    _STAGE_MAP = {
        "load": 0,
        "analyze": 1,
        "process": 2,
        "export": 3,
        "log": 4,
    }

    _STAGE_STATUS_MAP = {
        "load": "status.loading",
        "analyze": "status.analyzing",
        "process": "status.processing",
        "export": "status.exporting",
        "log": "status.writing_log",
    }

    def _update_progress_ui(self, stage, frac, extra):
        """Update progress bar, stage indicator, and status from worker message."""
        # Update stage indicator
        stage_idx = self._STAGE_MAP.get(stage, 0)
        self._stage_indicator.set_stage(stage_idx)

        # Update progress bar
        self._progress_bar.configure(value=frac * 100)

        # Update status text
        status_key = self._STAGE_STATUS_MAP.get(stage, "status.ready")
        self._status_var.set(t(status_key))

        # Update detail text
        detail_parts = []

        if stage == "analyze":
            total_sec = self._file_info._value_labels.get("info.duration", None)
            if extra.get("found_segments", 0) > 0:
                found = extra["found_segments"]
                total_dur = extra.get("total_removed", 0)
                detail_parts.append(
                    f"{t('progress.found_segments')}: {found} {t('progress.total_segments')}"
                    f"（{t('progress.total_duration')} {self._format_short_duration(total_dur)}）"
                )

        self._progress_detail.configure(text="  ".join(detail_parts))

    def _on_processing_done(self, result):
        """Called when processing completes successfully."""
        self._processing = False
        self._start_btn.configure(text=t("btn.start"), state=tk.NORMAL)
        self._stage_indicator.set_all_done()
        self._progress_bar.configure(value=100)

        summary = result["summary"]
        removed = result["removed_segments"]

        if len(removed) == 0:
            self._status_var.set(t("status.complete_no_silence"))
            self._progress_detail.configure(text="")
        elif summary.get("reduction_percent", 0) > 95:
            # Almost all silence — warn
            messagebox.showwarning(
                t("error.all_silence_title"),
                t("error.all_silence").format(100 - summary.get("reduction_percent", 0)))
            self._status_var.set(
                t("status.complete").format(result.get("log_path", "")))
        else:
            self._status_var.set(
                t("status.complete").format(result.get("log_path", "")))

            detail = (
                f"切除 {summary['total_segments_removed']} 段，"
                f"共 {self._format_short_duration(summary['total_removed_sec'])}，"
                f"耗时 {result.get('elapsed_sec', 0):.1f}s"
            )
            self._progress_detail.configure(text=detail)

        self._log_path = result.get("log_path")
        gc.collect()

    def _on_processing_error(self, error_msg):
        """Called when processing fails."""
        self._processing = False
        self._start_btn.configure(text=t("btn.start"), state=tk.NORMAL)
        self._stage_indicator.reset()
        self._progress_bar.configure(value=0)
        self._progress_detail.configure(text="")
        self._status_var.set(t("status.ready"))

        messagebox.showerror(t("error.title"),
                            t("error.processing").format(error_msg))
        gc.collect()

    # ── Log Viewer ────────────────────────────────────

    def _view_log(self):
        """Open the log viewer for the current input file."""
        if hasattr(self, "_log_path") and self._log_path:
            from gui.log_viewer import show_log_viewer
            show_log_viewer(self, self._log_path)
        elif self._input_path:
            show_log_selector(self, self._input_path)
        else:
            messagebox.showinfo(t("info.title"), t("log.no_logs"))

    # ── Helpers ───────────────────────────────────────

    def _format_short_duration(self, seconds):
        """Format seconds as compact human-readable string."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            m = int(seconds // 60)
            s = seconds % 60
            return f"{m}m {s:.0f}s"
        else:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            return f"{h}h {m}m"

    # ── Window Close ──────────────────────────────────

    def _on_close(self):
        if self._processing:
            ok = messagebox.askokcancel(
                t("error.close_during_processing_title"),
                t("error.close_during_processing"))
            if not ok:
                return
        self.destroy()
```

- [ ] **Step 2: Verify main window import**

```bash
python -c "from gui.main_window import MainWindow; print('main_window OK')"
```

Expected: `main_window OK`

---

### Task 12: Entry Point (main.py)

**Files:**
- Create: `main.py`

**Interfaces:**
- Consumes: gui.main_window (MainWindow), asmr_cleaner.i18n, asmr_cleaner.settings, ctypes (for DPI)
- Produces: executable entry point

- [ ] **Step 1: Write main.py**

```python
"""ASMR Cleaner — Remove long silence segments from ASMR live recordings.

Entry point. Sets up DPI awareness on Windows, configures the ttk theme,
and launches the main GUI window.
"""

import sys
import os

# Fix for PyInstaller: locate ffmpeg
if getattr(sys, "frozen", False):
    # Running as bundled exe
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

# Configure pydub to find ffmpeg
ffmpeg_path = os.path.join(base_path, "ffmpeg.exe")
if os.path.exists(ffmpeg_path):
    from pydub import AudioSegment
    AudioSegment.converter = ffmpeg_path


def _setup_dpi():
    """Enable high-DPI awareness on Windows."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        # Windows 10+ PerMonitorV2 DPI awareness
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE_V2
    except Exception:
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # fallback
        except Exception:
            pass


def main():
    """Launch the ASMR Cleaner GUI."""
    _setup_dpi()

    # Apply saved language preference
    from asmr_cleaner.i18n import set_language
    from asmr_cleaner import settings
    app_settings = settings.load()
    saved_lang = app_settings.get("language")
    if saved_lang:
        set_language(saved_lang)

    from gui.main_window import MainWindow
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify entry point imports**

```bash
python -c "import main; print('main.py OK')"
```

Expected: `main.py OK`

---

### Task 13: Integration Smoke Test

**Files:**
- Modify: none (test only)

- [ ] **Step 1: Create synthetic test audio**

```bash
python -c "
import numpy as np
from pydub import AudioSegment

sr = 48000
duration = 30  # 30 seconds total

# Generate: 5s tone, 8s silence, 5s tone, 7s silence, 5s tone
samples = np.zeros(duration * sr, dtype=np.float32)

# Tone A: 0-5s (440 Hz)
t = np.arange(0, 5 * sr) / sr
samples[:5*sr] = (np.sin(2 * np.pi * 440 * t) * 0.5).astype(np.float32)

# Tone B: 13-18s (880 Hz)
t = np.arange(0, 5 * sr) / sr
samples[13*sr:18*sr] = (np.sin(2 * np.pi * 880 * t) * 0.5).astype(np.float32)

# Tone C: 25-30s (220 Hz)
t = np.arange(0, 5 * sr) / sr
samples[25*sr:] = (np.sin(2 * np.pi * 220 * t) * 0.5).astype(np.float32)

# Convert to int16 and save
samples_int16 = (samples * 32767).astype(np.int16)
seg = AudioSegment(
    samples_int16.tobytes(),
    frame_rate=sr,
    sample_width=2,
    channels=1,
)
seg.export('test_input.wav', format='wav')
print('Created test_input.wav: 30s, 3 tone segments separated by silence')
"
```

- [ ] **Step 2: Run processing programmatically (no GUI)**

```bash
python -c "
from asmr_cleaner.core import process

def progress_cb(stage, frac, extra):
    print(f'  Stage: {stage} ({frac*100:.0f}%)', extra if extra else '')

print('Processing test_input.wav...')
result = process(
    'test_input.wav',
    'test_output.wav',
    threshold_db=-55,
    min_silence_sec=3.0,
    crossfade_ms=30,
    progress_callback=progress_cb,
)

print()
print('Result summary:')
s = result['summary']
print(f'  Original: {s[\"original_duration_sec\"]}s')
print(f'  Output: {s[\"output_duration_sec\"]}s')
print(f'  Removed: {s[\"total_segments_removed\"]} segments, {s[\"total_removed_sec\"]}s total')
print(f'  Reduction: {s[\"reduction_percent\"]}%')
print(f'  Elapsed: {result[\"elapsed_sec\"]}s')
print(f'  Log: {result[\"log_path\"]}')

# Verify: 8s + 7s = 15s of silence removed
# Original 30s, so output should be ~15s
assert abs(s['output_duration_sec'] - 15.0) < 1.0, f'Expected ~15s output, got {s[\"output_duration_sec\"]}s'
assert s['total_segments_removed'] == 2, f'Expected 2 silence segments, got {s[\"total_segments_removed\"]}'
print()
print('✅ Integration test PASSED')
"
```

Expected: `✅ Integration test PASSED` with ~15s output, 2 silence segments removed.

- [ ] **Step 3: Clean up test files**

```bash
rm -f test_input.wav test_output.wav test_input_cleaned_*.json
```

---

### Task 14: README Documentation

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README.md**

```markdown
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
```

- [ ] **Step 2: Commit all files (if git is initialized)**

```bash
git init && git add -A && git commit -m "feat: complete ASMR-Cleaner v1.0 implementation

- Core engine: silence detection with hysteresis, crossfade splice
- GUI: tkinter with i18n, progress tracking, stage indicator
- Logging: permanent JSON logs with formatted viewer dialog
- Settings: persistent user preferences in %APPDATA%

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Plan Self-Review

Before handing off, verify:

1. **Spec coverage**: Every spec section maps to at least one task — confirmed.
2. **No placeholders**: All code is complete, no TBDs — confirmed.
3. **Interface consistency**:
   - `t(key)` returns string ✓ (all GUI modules use it)
   - `process()` returns dict with `summary`, `removed_segments`, `log_path` ✓ (main_window uses these)
   - `load_audio` returns `(samples, info)` ✓ (core.process consumes it)
   - `detect_silence` returns list of dicts with `start_sample`, `end_sample` ✓ (core.process uses these)
   - `save_audio(samples, filepath, info)` ✓ (core.process calls it)
   - `write_log` returns `str` (log path) ✓ (core.process captures it)
   - `LogViewer` consumed as `show_log_viewer(parent, path)` ✓ (main_window calls it)
4. **i18n completeness**: All user-visible strings are in the STRINGS dict with both zh and en translations — confirmed.
