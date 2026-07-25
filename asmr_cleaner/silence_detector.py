"""Silence detection via RMS analysis with hysteresis state machine."""

import numpy as np

# Number of samples per analysis frame
FRAME_SIZE = 1024
# Floor value for dB calculation to avoid log10(0) = -inf
EPSILON = 1e-10


def _frames_rms_db(mono_samples):
    """Compute RMS (in dB) for each frame of mono audio.

    Args:
        mono_samples: 1D float32 array, normalized [-1.0, 1.0]

    Returns:
        frame_db: 1D float32 array of dB values, one per frame
        num_frames: total number of frames
    """
    total = len(mono_samples)
    num_frames = total // FRAME_SIZE
    if num_frames < 1:
        return np.array([], dtype=np.float32), 0
    # Trim to exact multiple
    trimmed = mono_samples[:num_frames * FRAME_SIZE]

    # Reshape into frames and compute RMS
    frames = trimmed.reshape(num_frames, FRAME_SIZE)
    rms = np.sqrt(np.mean(frames ** 2, axis=1))

    # Convert to dB with floor
    db = 20.0 * np.log10(np.maximum(rms, EPSILON))
    return db, num_frames


def detect_silence(samples, sample_rate, threshold_db, min_duration_sec,
                   hysteresis_ms=200, progress_callback=None):
    """Find all silence segments in audio.

    Uses a hysteresis state machine to prevent threshold-edge flickering.
    The analysis is frame-based: audio is divided into frames of FRAME_SIZE
    (1024) samples. Each frame's RMS level (in dB) is compared against
    threshold_db to classify it as silent or active. This means silence
    boundaries are quantized to frame boundaries (~21 ms resolution at
    48 kHz).

    Multi-channel audio is averaged to mono for detection by taking the
    mean across channels. The mono signal is then split into frames for
    analysis. The hysteresis window prevents rapid toggling at the edge
    of a silent region: the state machine only transitions from silence
    back to active after hysteresis_frames consecutive non-silent frames.

    Args:
        samples: float32 ndarray, shape (N,) mono or (N, C) multi-channel,
                 normalized to [-1.0, 1.0]
        sample_rate: samples per second (e.g. 48000)
        threshold_db: dB threshold — below this is considered silence
        min_duration_sec: minimum silence duration to report (seconds)
        hysteresis_ms: hysteresis window in milliseconds (default 200)
        progress_callback: callable(progress_0_to_1) called periodically
                           every ~100 frames (~2 s at 48 kHz)

    Returns:
        List of dicts, each with keys:
            start_sec, end_sec, duration_sec, start_sample, end_sample
            Returns an empty list for audio shorter than FRAME_SIZE samples
            or containing no silence intervals meeting min_duration_sec.
    """
    # Convert to mono for detection (average channels)
    if samples.ndim > 1 and samples.shape[1] > 1:
        mono = samples.mean(axis=1)
    else:
        mono = samples.flatten()

    # Compute per-frame dB
    frame_db, num_frames = _frames_rms_db(mono)

    # Convert parameters to frame counts
    frames_per_sec = sample_rate / FRAME_SIZE
    min_silence_frames = int(min_duration_sec * frames_per_sec)
    hysteresis_frames = max(1, int(hysteresis_ms / 1000.0 * frames_per_sec))

    if min_silence_frames < 1:
        min_silence_frames = 1

    # State machine: find silence intervals
    # State: 0 = in active audio, 1 = in silence
    state = 0  # start assuming active
    silence_start_frame = 0
    below_counter = 0   # consecutive frames below threshold
    above_counter = 0   # consecutive frames above threshold

    silence_intervals = []

    for i in range(num_frames):
        is_silent = frame_db[i] < threshold_db

        if state == 0:
            # Currently in active audio
            if is_silent:
                below_counter += 1
                if below_counter == 1:
                    silence_start_frame = i
                if below_counter >= min_silence_frames:
                    # Transition to silence
                    state = 1
                    above_counter = 0
                # else: haven't hit min_silence_frames yet, stay in state 0
            else:
                below_counter = 0
        else:
            # Currently in silence
            if not is_silent:
                above_counter += 1
                if above_counter >= hysteresis_frames:
                    # Transition back to active — record the silence
                    end_frame = i - hysteresis_frames + 1
                    silence_intervals.append({
                        "start_frame": silence_start_frame,
                        "end_frame": end_frame,
                    })
                    state = 0
                    below_counter = 0
            else:
                above_counter = 0

        # Progress callback
        if progress_callback and i % 100 == 0:
            progress_callback(i / num_frames)

    # Handle trailing silence (file ends while still in silence)
    if state == 1:
        silence_intervals.append({
            "start_frame": silence_start_frame,
            "end_frame": num_frames,
        })

    # Convert frame indices to time and sample indices
    result = []
    for interval in silence_intervals:
        start_sample = interval["start_frame"] * FRAME_SIZE
        end_sample = min(interval["end_frame"] * FRAME_SIZE, len(mono))
        start_sec = start_sample / sample_rate
        end_sec = end_sample / sample_rate
        duration_sec = end_sec - start_sec

        # Only keep intervals that meet the minimum duration
        if duration_sec >= min_duration_sec:
            result.append({
                "start_sec": start_sec,
                "end_sec": end_sec,
                "duration_sec": duration_sec,
                "start_sample": start_sample,
                "end_sample": end_sample,
            })

    return result
