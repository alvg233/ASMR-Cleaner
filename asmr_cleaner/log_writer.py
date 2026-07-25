"""Permanent JSON logging for processing results."""

import json
import os
import glob
from datetime import datetime


LOG_VERSION = "1.0"


def _build_log_filename(input_path):
    """Build log filename: {basename}_cleaned_{timestamp}.json"""
    base = os.path.splitext(os.path.basename(input_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base}_cleaned_{timestamp}.json"


def write_log(input_path, output_path, params, input_info,
              removed_segments, summary):
    """Write processing log as JSON. Uses atomic write (tmp + rename).

    Returns the path to the written log file.
    """
    log = {
        "version": LOG_VERSION,
        "input_file": os.path.abspath(input_path),
        "output_file": os.path.abspath(output_path),
        "processed_at": datetime.now().isoformat(),
        "parameters": params,
        "input_info": input_info,
        "removed_segments": removed_segments,
        "summary": summary,
    }

    # Write to same directory as output file
    output_dir = os.path.dirname(os.path.abspath(output_path))
    filename = _build_log_filename(input_path)
    log_path = os.path.join(output_dir, filename)

    # Atomic write
    tmp_path = log_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, log_path)

    return log_path


def read_log(log_path):
    """Read and parse a log JSON file. Returns dict or raises on error."""
    with open(log_path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_logs_for_file(input_path):
    """Find all log files associated with an input file.

    Looks in the same directory as the input file for files matching
    the pattern {basename}_cleaned_*.json

    Returns list of absolute paths, sorted by modification time (newest first).
    """
    directory = os.path.dirname(os.path.abspath(input_path))
    base = os.path.splitext(os.path.basename(input_path))[0]
    pattern = os.path.join(directory, f"{base}_cleaned_*.json")
    matches = glob.glob(pattern)
    matches.sort(key=os.path.getmtime, reverse=True)
    return matches
