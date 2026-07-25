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
