# This script reduces the size of a SpikeGLX dataset by selecting a time range around a few stim/trial events.
# It's intended to produce a valid dataset that we can process with pipeline code.
# Having a smaller, valid dataset is useful for testing -- this makes it easier to test early and test often!

from pathlib import Path

from utils import event_time_range, extract_bin, extract_behavior_events, extract_behavior_details

# This is a directory to receive extracted outputs.
minimal_dir = '/home/ninjaben/codin/geffen-lab-data/minimal-ecephys'

# This is the behavior events text file.
behavior_events = '/home/ninjaben/codin/geffen-lab-data/raw-ecephys/AS20_03112025_trainingSingle6Tone2024_behavior/AS20_031125_trainingSingle6Tone2024_0_39.txt'

# This is the behavior full-data .mat file.
behavior_details = '/home/ninjaben/codin/geffen-lab-data/raw-ecephys/AS20_03112025_trainingSingle6Tone2024_behavior/AS20_031125_trainingSingle6Tone2024_0_39.mat'

# This is the SpikeGLX run directory with nidq .bin and .meta files, and probe subdirectories.
spikeglx_dir = '/home/ninjaben/codin/geffen-lab-data/raw-ecephys/AS20_03112025_trainingSingle6Tone2024_Snk3.1_g0'

# This is a .txt file, relative to spikeglx_dir, with stim/trial event times.
# This could come from running CatGT for the SpikeGLX run.
# Here is an example CatGT comand to extrct event times but not do any binary data filtering:
#   runit.sh -dir=. -run=AS20_03112025_trainingSingle6Tone2024_Snk3.1 -g=0 -t=0 -ni -ap -prb_fld -out_prb_fld -prb=0 -no_tshift -xa=0,0,0,1,3,500 -xia=0,0,1,3,3,0 -xd=0,0,8,3,0 -xid=0,0,-1,2,1.7 -xid=0,0,-1,3,5
trial_events = 'AS20_03112025_trainingSingle6Tone2024_Snk3.1_g0_tcat.nidq.xd_8_3_0.txt'

# This is the nidq .bin file (and corresponding .meta), relative to spikeglx_dir.
nidq_bin_file = 'AS20_03112025_trainingSingle6Tone2024_Snk3.1_g0_t0.nidq.bin'

# This is an ap .bin file (and corresponding .meta), relative to spikeglx_dir.
ap_bin_file = 'AS20_03112025_trainingSingle6Tone2024_Snk3.1_g0_imec0/AS20_03112025_trainingSingle6Tone2024_Snk3.1_g0_t0.imec0.ap.bin'

# This amounts to a range of time to extract, based on trials and some padding.
start_trial = 0
end_trial = 3
trial_padding_seconds = 1.5

# Extract relevant lines from the behavior .txt file.
behavior_events_in = Path(behavior_events)
behavior_events_out = Path(minimal_dir, "behavior", behavior_events_in.name)
extract_behavior_events(
    behavior_events_in,
    behavior_events_out,
    start_trial,
    end_trial
)

# Extract relevant details from the behavior .mat file.
behavior_details_in = Path(behavior_details)
behavior_details_out = Path(minimal_dir, "behavior", behavior_details_in.name)
extract_behavior_details(
    behavior_details_in,
    behavior_details_out,
    start_trial,
    end_trial
)

# Choose the time range to extract from the sampled data files.
trial_events_path = Path(spikeglx_dir, trial_events)
(start_time, end_time) = event_time_range(trial_events_path, start_trial, end_trial, trial_padding_seconds)

# Extract relevant samples from the nidq .bin file.
minimal_path = Path(minimal_dir)
nidq_bin_in = Path(spikeglx_dir, nidq_bin_file)
nidq_bin_out = Path(minimal_path, "ecephys", nidq_bin_file)
extract_bin(nidq_bin_in, nidq_bin_out, start_time, end_time)

# Extract relevant samples from the ap .bin file.
ap_bin_in = Path(spikeglx_dir, ap_bin_file)
ap_bin_out = Path(minimal_path, "ecephys", ap_bin_file)
extract_bin(ap_bin_in, ap_bin_out, start_time, end_time)
