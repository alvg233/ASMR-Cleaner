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
