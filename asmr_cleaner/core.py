"""Core processing engine — orchestrates load -> detect -> cut -> crossfade -> save -> log."""

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
        # Caller (process) must handle empty arrays with the correct channel count
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

    crossfade_frames = round(crossfade_ms / 1000.0 * info["sample_rate"])

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
        if len(retained) == 0:
            # All content was silence — create empty array with correct channel count
            output_samples = np.zeros((0, info["channels"]), dtype=np.float32)
        else:
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
