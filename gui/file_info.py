"""File info panel — displays audio file metadata."""

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
            lbl.configure(text=t("error.title") if key == "info.format" else "—")

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
