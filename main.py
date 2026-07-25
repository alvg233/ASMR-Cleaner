"""ASMR Cleaner — Remove long silence segments from ASMR live recordings.

Entry point. Sets up DPI awareness on Windows, configures the ttk theme,
and launches the main GUI window.
"""

import sys
import os

# --- ffmpeg / ffprobe discovery ---
# Must happen BEFORE any pydub import, because pydub scans PATH at import time.
if getattr(sys, "frozen", False):
    _base_path = sys._MEIPASS
else:
    _base_path = os.path.dirname(os.path.abspath(__file__))

# Add project dir to PATH so pydub's `which("ffmpeg")` finds it silently
_ffmpeg_dir = _base_path
if os.path.exists(os.path.join(_base_path, "ffmpeg.exe")):
    os.environ["PATH"] = _ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
    # Also set explicitly for any edge case where pydub ignores PATH
    import pydub.utils
    pydub.utils.FFMPEG_PATH = os.path.join(_base_path, "ffmpeg.exe")
    pydub.utils.FFPROBE_PATH = os.path.join(_base_path, "ffprobe.exe")


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
