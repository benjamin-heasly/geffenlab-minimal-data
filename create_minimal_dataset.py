import sys
from pathlib import Path

from utils import locate_input_paths, event_time_range, extract_bin, extract_behavior_events, extract_behavior_details


# Parse command line inputs.
# If this gets more complicated we should switch to Argparse
#   https://docs.python.org/3/library/argparse.html
#
# Usage:
#   python create_minimal_dataset.py minimal_out/ behavior_in/ spikeglx_in/ tprime_in/ *trial_events.txt start_trial end_trial padding_seconds

minimal_dir = sys.argv[1]

behavior_dir = sys.argv[2]
spikeglx_dir = sys.argv[3]
tprime_dir = sys.argv[4]
trial_events_pattern = sys.argv[5]
input_paths = locate_input_paths(behavior_dir, spikeglx_dir, tprime_dir, trial_events_pattern)

start_trial = int(sys.argv[6])
end_trial = int(sys.argv[7])
trial_padding_seconds = float(sys.argv[8])

# Extract relevant lines from the behavior .txt file.
behavior_events_in = input_paths["behavior_events"]
behavior_events_out = Path(minimal_dir, "behavior", behavior_events_in.name)
extract_behavior_events(
    behavior_events_in,
    behavior_events_out,
    start_trial,
    end_trial
)

# Extract relevant details from the behavior .mat file.
behavior_details_in = input_paths["behavior_details"]
behavior_details_out = Path(minimal_dir, "behavior", behavior_details_in.name)
extract_behavior_details(
    behavior_details_in,
    behavior_details_out,
    start_trial,
    end_trial
)

# Choose the time range to extract from the sampled data files.
trial_events_path = input_paths["trial_events"]
(start_time, end_time) = event_time_range(trial_events_path, start_trial, end_trial, trial_padding_seconds)

# Extract relevant samples from the nidq .bin file.
nidq_bin_in = input_paths["nidq_bin_file"]
ecephys_base = nidq_bin_in.parent.parent
nidq_bin_out = Path(minimal_dir, "ecephys", nidq_bin_in.relative_to(ecephys_base))
extract_bin(nidq_bin_in, nidq_bin_out, start_time, end_time)

# Extract relevant samples from the ap .bin file.
ap_bin_in = input_paths["ap_bin_file"]
ap_bin_out = Path(minimal_dir, "ecephys", ap_bin_in.relative_to(ecephys_base))
extract_bin(ap_bin_in, ap_bin_out, start_time, end_time)
