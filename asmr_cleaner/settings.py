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
