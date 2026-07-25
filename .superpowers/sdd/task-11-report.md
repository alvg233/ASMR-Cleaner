# Task 11 Report: GUI Main Window

## Summary

Created `gui/main_window.py` — the central GUI assembly that integrates all previously built modules into a cohesive application window.

## File Created

- `F:\dev\ASMR-Cleaner\gui\main_window.py` — `MainWindow(tk.Tk)` class

## Key Design Decisions

**Thread model:** A daemon worker thread runs `asmr_cleaner.core.process()`, pushing progress tuples `("progress", stage, frac, extra)` into a `queue.Queue`. The main thread polls this queue every 100ms via `self.after(100, self._poll_progress)`. The worker thread never touches tkinter widgets.

**5-stage progress pipeline:** Maps `core.process()` callback stage names (`load`, `analyze`, `process`, `export`, `log`) to the `StageIndicator`'s 0-based index. Status bar updates are driven by a stage-to-status-key dictionary.

**Language menu:** Settings -> Language -> 中文 / English radiobuttons bound to a shared `tk.StringVar`. Switching language updates settings.json and shows a restart-notice dialog.

**Safety guards:**
- File size > 2 GB triggers an `askokcancel` warning before processing
- Existing output file triggers an overwrite confirmation dialog
- Window close during processing prompts for confirmation; the daemon thread is killed on exit
- Start button is disabled until a file is selected and re-disabled during processing

**Parameter frame:** Three `LabeledSlider` widgets reading default values from `settings.load()`, covering threshold (-90 to -20 dB), min silence (0.5 to 60 s), and crossfade (5 to 200 ms).

**Log viewer integration:** The "View Log" button first checks for a recent `_log_path` from the current session, falling back to `show_log_selector()` which hunts for log files matching the input filename.

## Verification

```
python -c "from gui.main_window import MainWindow; print('main_window OK')"
```
Output: `main_window OK`

## Dependencies Consumed

| Module | Interfaces Used |
|---|---|
| `asmr_cleaner.i18n` | `t()`, `set_language()`, `get_language()` |
| `asmr_cleaner.settings` | `load()`, `save()` |
| `asmr_cleaner.audio_io` | `get_audio_info()`, `SUPPORTED_FORMATS` |
| `asmr_cleaner.core` | `process()` |
| `gui.widgets` | `LabeledSlider`, `StageIndicator` |
| `gui.file_info` | `FileInfoPanel` |
| `gui.log_viewer` | `show_log_selector`, `show_log_viewer` |
