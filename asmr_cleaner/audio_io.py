"""Audio file I/O. Wraps pydub for format decode/encode, uses numpy for data."""

import json
import os
import subprocess
import numpy as np
from pydub import AudioSegment

# Supported input formats (by extension, uppercase)
SUPPORTED_FORMATS = {".WAV", ".MP3", ".FLAC", ".AAC", ".OGG", ".M4A", ".WMA"}


def _get_ffprobe_path():
    """Find ffprobe executable. Uses pydub's cached path if set."""
    import pydub.utils
    path = getattr(pydub.utils, 'FFPROBE_PATH', None)
    if path and os.path.exists(path):
        return path
    # Fallback: search PATH
    for p in os.environ.get("PATH", "").split(os.pathsep):
        candidate = os.path.join(p, "ffprobe.exe" if os.name == "nt" else "ffprobe")
        if os.path.exists(candidate):
            return candidate
    return "ffprobe"  # hope it's on PATH


def get_audio_info(filepath):
    """Read audio metadata via ffprobe — fast, no audio decoding.

    Returns dict with keys: format, sample_rate, bit_depth, channels,
    duration_sec, file_size_bytes.
    """
    ext = os.path.splitext(filepath)[1].upper()
    if ext not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format: {ext}")

    ffprobe = _get_ffprobe_path()

    # ffprobe JSON query for stream info
    cmd = [
        ffprobe, "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams",
        "-select_streams", "a:0",  # first audio stream only
        filepath,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        result.check_returncode()
        data = json.loads(result.stdout)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError) as e:
        raise ValueError(f"Cannot read file metadata: {e}")

    # Extract stream info
    streams = data.get("streams", [])
    if not streams:
        raise ValueError("No audio stream found in file")

    stream = streams[0]
    fmt = data.get("format", {})

    # Parse duration: prefer stream duration, fall back to format duration
    duration_str = stream.get("duration") or fmt.get("duration")
    duration_sec = float(duration_str) if duration_str else 0.0

    # Parse sample rate
    sample_rate = int(stream.get("sample_rate", 0))

    # Parse channels
    channels = int(stream.get("channels", 1))

    # Bit depth: try stream's bits_per_raw_sample, then bits_per_sample,
    # then codec_name heuristics, default 16
    bit_depth_str = stream.get("bits_per_raw_sample") or stream.get("bits_per_sample")
    if bit_depth_str:
        bit_depth = int(bit_depth_str)
    else:
        codec = stream.get("codec_name", "")
        if "32" in codec or stream.get("sample_fmt", "").startswith("s32"):
            bit_depth = 32
        elif "24" in codec:
            bit_depth = 24
        elif "flac" in codec:
            bit_depth = int(stream.get("bits_per_raw_sample", 16))
        else:
            bit_depth = 16

    file_size = os.path.getsize(filepath)

    return {
        "format": ext.lstrip("."),
        "sample_rate": sample_rate,
        "bit_depth": bit_depth,
        "channels": channels,
        "duration_sec": duration_sec,
        "file_size_bytes": file_size,
    }


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
        raise ValueError(f"Unsupported format: {ext}")

    # Get metadata fast via ffprobe
    info = get_audio_info(filepath)

    # Full decode via pydub
    seg = AudioSegment.from_file(filepath)

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
