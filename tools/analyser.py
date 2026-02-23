import h5py
import tqdm
import numpy as np
import pandas as pd
from signals.PeakSignal import PeakSignal
from scipy.interpolate import UnivariateSpline


def repair_waveform(t, wf):
    nan_mask = np.isnan(wf)
    if not np.any(nan_mask):
        return wf

    t_valid = t[~nan_mask]
    wf_valid = wf[~nan_mask]

    if len(t_valid) < 4:
        return wf

    spline = UnivariateSpline(t_valid, wf_valid, k=3, s=0)

    wf_repaired = wf.copy()
    wf_repaired[nan_mask] = spline(t[nan_mask])
    return wf_repaired


def analyse_waveforms(file_path, voltage):
    rows = []

    with h5py.File(file_path, "r") as f:
        group_key = f"voltage_{int(voltage):04d}V"
        if group_key not in f:
            print(f"Warning: {group_key} not found in file.")
            return pd.DataFrame()

        voltage_grp = f[group_key]
        pos_keys = [key for key in voltage_grp.keys() if key.startswith("pos_")]

        for pos_key in tqdm.tqdm(pos_keys, desc=f"Processing {voltage}V"):
            pos_grp = voltage_grp[pos_key]

            x = round(pos_grp.attrs["x"] * 1e6)
            y = round(pos_grp.attrs["y"] * 1e6)
            z = round(pos_grp.attrs["z"] * 1e6)

            ch_datasets = [
                k for k in pos_grp.keys() if k.startswith("ch") and k.endswith("_v")
            ]
            for ds_name in ch_datasets:
                ch_num = int(ds_name.split("_")[0].replace("ch", ""))
                ch_data = pos_grp[ds_name]

                dt = ch_data.attrs["dt"]
                t0 = ch_data.attrs["t0"]

                n_samples = ch_data.shape[1]
                half = n_samples // 2

                t = (t0 + np.arange(n_samples) * dt) * 1e9

                t_first_half = t[:half]
                t_second_half = t[half:]

                waveforms = ch_data[:]

                for idx, wf in enumerate(waveforms):

                    wf_pulses = [
                        (wf[:half], t_first_half, 1),
                        (wf[half:], t_second_half, 2),
                    ]

                    for wf_part, t_part, pulse_num in wf_pulses:
                        if np.isnan(wf_part).any():
                            wf_part = repair_waveform(t_part, wf_part)

                        try:
                            signal = PeakSignal(t_part, wf_part, peak_polarity="guess")

                            row_data = {
                                "x": x,
                                "y": y,
                                "z": z,
                                "ch": ch_num,
                                "waveform_index": idx,
                                "pulse_number": pulse_num,
                                "peak_amplitude": signal.amplitude,
                                "peak_integral": signal.peak_integral,
                            }

                            for threshold in range(20, 91, 10):
                                col = f"peak_time_{threshold}"
                                row_data[col] = signal.find_time_at_rising_edge(
                                    threshold
                                )

                            rows.append(row_data)

                        except Exception:
                            continue

    return pd.DataFrame(rows)


def save_analysis(df, file_path):
    with open(file_path, "w") as f:
        df.to_csv(f, index=False)


def read_analysis(file_path):
    with open(file_path, "r") as f:
        return pd.read_csv(f)
