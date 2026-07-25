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
