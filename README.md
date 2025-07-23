# geffenlab-minimal-data

This repo contains scripts for making a "minimal dataset" from Geffen lab data.
This means extracting neural and behavioral data from just a few trials, out of a full session.
The extracted dataset should remain intact, in the sense that neural and behavior data are still aligned, and metadata are updated to agree with the smaller dataset.
A minimal dataset should be able to flow through the same processing steps as a full dataset, in less time.

Minimal datasets like this are not intended for analysis and publication.
But they are quite useful for testing code -- especially in different environments that might not have large storage capacity or compute power.

# Environment setup

Get Python and dependencies in a [conda](https://www.anaconda.com/docs/getting-started/miniconda/main) environment.

```
conda env create -f environment.yml
conda activate minimal-dataset
```

Get [CatGT](https://github.com/billkarsh/CatGT) for locating trial/stim event times across the session.

```
cd geffen-lab-data/raw-ecephys
wget https://billkarsh.github.io/SpikeGLX/Support/CatGTLnxApp.zip
unzip CatGTLnxApp.zip
cd CatGT-linux/
chmod +x ./install.sh 
./install.sh 
```

# Session data

Get a full session of Geffen lab SpikeGLX and behavior data.
For example:

```
geffen-lab-data/raw-ecephys/
├── AS20_03112025_trainingSingle6Tone2024_behavior/
│   ├── AS20_031125_trainingSingle6Tone2024_0_39.mat
│   └── AS20_031125_trainingSingle6Tone2024_0_39.txt
└── AS20_03112025_trainingSingle6Tone2024_Snk3.1_g0/
    ├── AS20_03112025_trainingSingle6Tone2024_Snk3.1_g0_t0.nidq.bin
    ├── AS20_03112025_trainingSingle6Tone2024_Snk3.1_g0_t0.nidq.meta
    └── AS20_03112025_trainingSingle6Tone2024_Snk3.1_g0_imec0/
        ├── AS20_03112025_trainingSingle6Tone2024_Snk3.1_g0_t0.imec0.ap.bin
        └── AS20_03112025_trainingSingle6Tone2024_Snk3.1_g0_t0.imec0.ap.meta
```

# Find trial/stim event times with CatGT

Use CatGT to find trial/stim event times across the whole session.
We'll use these times when extracting recording `.bin` data from specific trials, below.

This CatGT command extracts the event times but doesn't filter or rewrite any recording `.bin` data.

```
cd geffen-lab-data/raw-ecephys
./CatGT-linux/runit.sh -dir=. -run=AS20_03112025_trainingSingle6Tone2024_Snk3.1 -g=0 -t=0 -ni -ap -prb_fld -out_prb_fld -prb=0 -no_tshift -xa=0,0,0,1,3,500 -xia=0,0,1,3,3,0 -xd=0,0,8,3,0 -xid=0,0,-1,2,1.7 -xid=0,0,-1,3,5
```

This should run quickly (less than a minute), since it's not filtering the recording `.bin` data.
It should produce several `.txt` files with extracted event times.

For this dataset, the only file we need below is `AS20_03112025_trainingSingle6Tone2024_Snk3.1_g0_tcat.nidq.xd_8_3_0.txt`:

```
geffen-lab-data/raw-ecephys
├── AS20_03112025_trainingSingle6Tone2024_Snk3.1_g0/
    └── AS20_03112025_trainingSingle6Tone2024_Snk3.1_g0_tcat.nidq.xd_8_3_0.txt
```

# Extract a minimal dataset

Use `create_minimal_dataset.py` to extract a few trial's-worth of data from the full recording.

The general usage is:

```
python create_minimal_dataset.py minimal_out/ behavior_in/ spikeglx_in/ tprime_in/ *trial_events.txt start_trial end_trial padding_seconds
```

This example would extract at trial/stim events 5-13, plus 1.5 seconds of padding on each side:


```
python create_minimal_dataset.py \
  /home/ninjaben/codin/geffen-lab-data/data/AS20-minimal2/03112025 \
  /home/ninjaben/codin/geffen-lab-data/data/AS20/03112025/behavior \
  /home/ninjaben/codin/geffen-lab-data/data/AS20/03112025/ecephys/AS20_03112025_trainingSingle6Tone2024_Snk3.1_g0 \
  /home/ninjaben/codin/geffen-lab-data/other/old-ecephys/home/ninjaben/ecephys_output/catgt_AS20_03112025_trainingSingle6Tone2024_Snk3.1_g0 \
  *nidq.xd_8_3_0.txt 5 13 1.5
```

The output should look like this:

```
geffen-lab-data/minimal-ecephys/
├── behavior/
│   ├── AS20_031125_trainingSingle6Tone2024_0_39.mat
│   └── AS20_031125_trainingSingle6Tone2024_0_39.txt
└── ecephys/
    └──AS20_03112025_trainingSingle6Tone2024_Snk3.1_g0
        ├── AS20_03112025_trainingSingle6Tone2024_Snk3.1_g0_t0.nidq.bin
        ├── AS20_03112025_trainingSingle6Tone2024_Snk3.1_g0_t0.nidq.meta
        └── AS20_03112025_trainingSingle6Tone2024_Snk3.1_g0_imec0/
            ├── AS20_03112025_trainingSingle6Tone2024_Snk3.1_g0_t0.imec0.ap.bin
            └── AS20_03112025_trainingSingle6Tone2024_Snk3.1_g0_t0.imec0.ap.meta
```

The output subdirs `behavior` and `ecephys` should match the data organization expected by [aind-ephys-pipeline (kilosort4)](https://codeocean.allenneuraldynamics.org/capsule/9352933/tree).

Here is an example minimal data asset at AIND Code Ocean: [ecephys_AS20_2025-03-11_11-08-51_v2](https://codeocean.allenneuraldynamics.org/data-assets/2429fd9e-80c5-4cf0-a281-9c8043cfc402/ecephys?filters=N4Igzg9gTgLiBcIDGUCmBDGqAmIA0I2qYSCMUArqgQA7oDmqCAjLalAAoNPwBMADAXTYAbugB2SHAmABfAgFsKAGxgBLAGJrV7MDJDokUsGAAyqEamV74AbWRpM0gLryQ49Ap4hUUmgAsATzAAfQBBAGUBEIFeAFYAWn4AZgTmZhD0pIAOBLiMkV58QmIUNRp1CHEEEAAVfzUwAAJGpvQmsE8aZVQm7Ex0MFQYJoAzaCaKIaaAdzUYfyaacqs1cV6sMHVxegA6JqaASRgAcmb2-ph21AAPckMRtBo0IfFt%2Bjax1Bmm8jV0axNCAUEYQUafZRVRhQJpoJDQbBrD5DExqKq7YpXeg2exQdAzYq%2BVD%2BGjBYqRAQgZwEADWa1wiEug2GxTAagAXjxmPwAJwAdjicQAbMkACzJAijbTEBBCgiQChQKT6aBqehrGqQpAAkBuGjsBSNNlVGygdBKhqWMiUaglHpYa1UAg4eaO21gfzmnjkJ0gERqb5ugj%2B74RT1oN1uLZOGpSjzKYoQGbrKCHBkgABGSAzQv4fOYowSvGS8QSou1PISPNF2V4CSzcVQqCz2D5hiKBCTKYAcp5vBnUOIAFaeNa7fwYMDKQIAAXoCnQ2l28IUxRQGCw2DCcHgzD5ourfL5QrifN22WycWyfJ52QIGeZAFUoAnEP4YDAaGB4AB6H-wogICkCRdgBHpxHWRUAWwQIPENJAwF2aB6B-JkhhgMAfyzHM8wLIsS0Sct0Erata3rJBG2bJBW3bH9eFFXgeVGbAeVQBJsn4CiyyQUZ%2BASdBeGyZgqyQDjxR4pBRX4DsQHpW4IiuB1EBXbphmkAgkCmGAIAUABZYZhAGfQmSaHpLFfEA8R%2BJlCRufUoDULw3l%2BQJ9RqIkAjJRQIH6ZR5kCdy7jxKRlGUFRzSaKxfHICBPONSF6AC%2BUKAzIdopadMKX4VkUrSpARjAfUkADGwQF0qYmiUEgVCmXUCGUQYYEOcQiBuaRd33Q8%2BSE-hdm6hipLiIR8rUSwAHlk10BBbFANR02w3N80LYtSyIkiazrBsmxbNskBkuD%2B0HEdDXEcdJ2nOcFyXFdCSuiyB2HUdTonQYLvnRdlGXHTdWpWTxBoEEABEjLsX71ycLcYFMdABwsgApChxCaHk8CaWI4iabl4H4bL6sa5rWpwaHYZqBGkZRtHpIxrGUlZDlUGJqwamYXZpKaABxAAhYpGmBq50MjIA).
