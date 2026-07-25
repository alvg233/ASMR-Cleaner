"""ASMR Cleaner — Remove long silence segments from ASMR live recordings.

Entry point. Sets up DPI awareness on Windows, configures the ttk theme,
and launches the main GUI window.
"""

import sys
import os

# --- ffmpeg / ffprobe discovery ---
# Must happen BEFORE any pydub import, because pydub scans PATH at import time.
# When frozen (PyInstaller), ffmpeg/ffprobe live next to the .exe, NOT inside the bundle.
if getattr(sys, "frozen", False):
    _exe_dir = os.path.dirname(sys.executable)
    # Also check _MEIPASS for the case where they ARE bundled (legacy)
    _search_dirs = [_exe_dir, sys._MEIPASS]
else:
    _exe_dir = os.path.dirname(os.path.abspath(__file__))
    _search_dirs = [_exe_dir]

for _d in _search_dirs:
    _ff = os.path.join(_d, "ffmpeg.exe")
    if os.path.exists(_ff):
        os.environ["PATH"] = _d + os.pathsep + os.environ.get("PATH", "")
        import pydub.utils
        pydub.utils.FFMPEG_PATH = _ff
        pydub.utils.FFPROBE_PATH = os.path.join(_d, "ffprobe.exe")
        break

# Suppress ffmpeg/ffprobe console popup on Windows
if sys.platform == "win32":
    import subprocess as _sp
    _orig = _sp.Popen
    class _NoConsolePopen(_orig):
        def __init__(self, *a, **kw):
            kw.setdefault('creationflags', 0)
            kw['creationflags'] |= 0x08000000  # CREATE_NO_WINDOW
            super().__init__(*a, **kw)
    _sp.Popen = _NoConsolePopen


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
