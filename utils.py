from pathlib import Path
from datetime import datetime
import hashlib

import numpy as np
from scipy.io import loadmat, savemat


def locate_input_paths(
    behavior_root: str,
    spikeglx_root: str,
    tprime_root: str,
    trial_events_pattern: str,
    behavior_mat_pattern: str = '*.mat',
    behavior_txt_pattern: str = '*.txt',
    spikeglx_nidq_pattern: str = '*.nidq.bin',
    spikeglx_ap_pattern: str = '**/*.ap.bin',
) -> dict[str, Path]:
    input_paths = {}

    behavior_path = Path(behavior_root)
    input_paths["behavior_events"] = list(behavior_path.glob(behavior_txt_pattern))[0]
    input_paths["behavior_details"] = list(behavior_path.glob(behavior_mat_pattern))[0]

    spikeglx_path = Path(spikeglx_root)
    input_paths["nidq_bin_file"] = list(spikeglx_path.glob(spikeglx_nidq_pattern))[0]
    input_paths["ap_bin_file"] = list(spikeglx_path.glob(spikeglx_ap_pattern))[0]

    tprime_path = Path(tprime_root)
    input_paths["trial_events"] = list(tprime_path.glob(trial_events_pattern))[0]

    print(f"Found input paths: {input_paths}")

    return input_paths


def event_time_range(
    events_file: Path,
    start_event: int = 0,
    end_event: int = 3,
    event_padding_seconds: float = 1.5
) -> tuple[float, float]:
    """Pick a time range, given a .txt file of event times and some padding to add before and after."""
    event_times = np.fromfile(events_file, dtype=float, sep="\n")
    start_time = event_times[start_event] - event_padding_seconds
    end_time = event_times[end_event] + event_padding_seconds

    duration = end_time - start_time
    print(f"Events {start_event}-{end_event} +/-{event_padding_seconds}s: {start_time}s - {end_time}s ({duration}s total)")

    return (start_time, end_time)


def parse_meta(meta_file: Path):
    """Parse a SpikeGLX .meta file into a Python dict."""
    meta_info = {}
    with open(meta_file, 'r') as f:
        for line in f:
            line_parts = line.split("=", maxsplit=1)
            key = line_parts[0].strip()
            if len(line_parts) > 1:
                raw_value = line_parts[1].strip()
                try:
                    value = int(raw_value)
                except:
                    try:
                        value = float(raw_value)
                    except:
                        value = raw_value
            else:
                value = None
            meta_info[key] = value
    return meta_info


def compute_sha1(
    bin_in: Path,
    buffer_size: int = 65536
):
    """Compute the sha1 digest for a binary file."""
    sha1 = hashlib.sha1()
    with open(bin_in, 'rb') as bin:
        while data := bin.read(buffer_size):
            sha1.update(data)

    digest = sha1.hexdigest().upper()
    return digest


def write_extract_meta(
    meta_in: Path,
    meta_out: Path,
    bin_out: Path,
    bin_out_sha1: str,
    total_bytes: int,
    total_duration: float,
    first_sample: int
):
    """Write a new .meta file to match an extracted .bin file."""
    print(f"Extract from {meta_in}")
    print(f"          to {meta_out}")

    meta_out.parent.mkdir(parents=True, exist_ok=True)

    run_date = datetime.now().replace(microsecond=0).isoformat(sep='T', timespec='auto')
    with open(meta_out, 'w') as file_out:
        with open(meta_in, 'r') as file_in:
            for line_in in file_in:
                # Replace selected lines to reflect the truncation.
                # Otherwise, pass through lines of the original file.
                if line_in.startswith("fileCreateTime="):
                    file_out.write(f"fileCreateTime={run_date}\n")
                elif line_in.startswith("fileName="):
                    file_out.write(f"fileName={bin_out.as_posix()}\n")
                elif line_in.startswith("fileSHA1="):
                    file_out.write(f"fileSHA1={bin_out_sha1}\n")
                elif line_in.startswith("fileSizeBytes="):
                    file_out.write(f"fileSizeBytes={total_bytes}\n")
                elif line_in.startswith("fileTimeSecs="):
                    file_out.write(f"fileTimeSecs={total_duration}\n")
                elif line_in.startswith("firstSample="):
                    file_out.write(f"firstSample={first_sample}\n")
                else:
                    file_out.write(line_in)

            # Write a final comment indicating that this file is an extract.
            file_out.write(f"~extracted=1\n")


def extract_bin(
    bin_in: Path,
    bin_out: Path,
    start_time: float,
    end_time: float,
    dtype: str = 'int16'
):
    """Extract a time range (rounded to whole samples) from the given .bin (and corresponding .meta)."""
    meta_in = bin_in.with_suffix('.meta')
    meta_info = parse_meta(meta_in)

    print(f"Extract from {bin_in}")
    print(f"          to {bin_out}")

    bin_out.parent.mkdir(parents=True, exist_ok=True)

    if 'niSampRate' in meta_info:
        sample_rate = meta_info['niSampRate']
    else:
        sample_rate = meta_info['imSampRate']

    start_sample = int(np.floor(start_time * sample_rate))
    end_sample = int(np.ceil(end_time * sample_rate))
    duration = end_time - start_time
    sample_count = end_sample - start_sample + 1
    print(f"          {start_time}s - {end_time}s ({duration}s total) at {sample_rate}Hz")

    channel_count = meta_info['nSavedChans']
    print(f"          samples {start_sample}-{end_sample} ({sample_count} total) from {channel_count} channels")

    shape_in = (-1, channel_count)
    data_in = np.memmap(bin_in, dtype=dtype, mode='r')
    data_in = data_in.reshape(shape_in)

    bin_out.parent.mkdir(parents=True, exist_ok=True)

    shape_out = (sample_count, channel_count)
    data_out = np.memmap(bin_out, dtype=dtype, mode='w+', shape=shape_out)
    data_out[:, :] = data_in[start_sample:end_sample + 1, :]
    data_out.flush()

    # Start the extracted binary at sample 0, as if this were the entire recording.
    meta_out = bin_out.with_suffix(".meta")
    total_bytes = channel_count * sample_count * data_out.itemsize
    bin_out_sha1 = compute_sha1(bin_out)
    write_extract_meta(
        meta_in,
        meta_out,
        bin_out,
        bin_out_sha1,
        total_bytes,
        duration,
        first_sample=0
    )


def extract_behavior_events(
    events_in: Path,
    events_out: Path,
    start_trial: int,
    end_trial: int,
):
    """Extract header, footer, and relevant trial lines from a behavior events .txt file."""

    print(f"Extract from {events_in}")
    print(f"          to {events_out}")
    print(f"          trials {start_trial}-{end_trial}")

    events_out.parent.mkdir(parents=True, exist_ok=True)

    with open(events_out, 'w') as file_out:
        with open(events_in, 'r') as file_in:
            for line_in in file_in:
                # Skip blank lines.
                if not line_in.strip():
                    continue

                # Parse each line as a tuple of space-separated strings.
                parts = line_in.split(" ")

                # The first tuple element might be a decimal trial number.
                trial_number = int(parts[0]) if parts[0].isdecimal() else None
                trial_index = trial_number - 1 if trial_number is not None else -1

                if trial_number is None:
                    # Keep header lines that have no trial number.
                    file_out.write(line_in)
                elif start_trial <= trial_index and trial_index <= end_trial:
                    # Keep lines relevant to the given trial range -- which is zero-based.
                    # Shift trial number to make the first in the range be trial number 0001.
                    shifted_trial_number = trial_index - start_trial + 1
                    trial_part = f"{shifted_trial_number:>04d}"
                    data_part = " ".join(parts[1:])
                    line_out = f"{trial_part} {data_part}"
                    file_out.write(line_out)
                elif trial_number == 0:
                    # Keep footer lines for trial zero.
                    file_out.write(line_in)
                else:
                    # Discard lines not relevant to the given trial range.
                    continue


def extract_behavior_details(
    details_in: Path,
    details_out: Path,
    start_trial: int,
    end_trial: int,
):
    """Extract relevant trials from a behavior details .mat file."""

    print(f"Extract from {details_in}")
    print(f"          to {details_out}")
    print(f"          trials {start_trial}-{end_trial}")

    details_out.parent.mkdir(parents=True, exist_ok=True)

    trial_range = range(start_trial, end_trial + 1)

    details = loadmat(details_in)
    details['tt'] = details['tt'][trial_range, :]
    details['resp'] = details['resp'][:, trial_range]
    details['correctionTrial'] = details['correctionTrial'][:, trial_range]
    details['lapsed'] = details['lapsed'][:, trial_range]
    details['reward'] = details['reward'][:, trial_range]
    details['lickSide'] = details['lickSide'][:, trial_range]

    details['trialStartPoint'] = np.array([[0]])
    details['trialEndPoint'][0] = np.array([[end_trial - start_trial]])

    savemat(details_out, details)
