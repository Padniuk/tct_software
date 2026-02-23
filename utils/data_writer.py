import h5py
from configs import config


class DataWriter:
    def __init__(self, filename, metadata):
        self.filename = filename
        self.file = h5py.File(filename, "w", libver="latest")
        for k, v in metadata.items():
            self.file.attrs[k] = v

    def write_position(self, voltage, current, n_pos, actual_pos, data_all_channels):
        v_grp_name = f"voltage_{voltage:04.0f}V"
        v_grp = self.file.require_group(v_grp_name)

        v_grp.attrs["voltage_V"] = voltage
        v_grp.attrs["bias_current_A"] = current

        grp = v_grp.create_group(f"pos_{n_pos:05d}")
        grp.attrs["x"], grp.attrs["y"], grp.attrs["z"] = actual_pos

        for ch_idx, triggers in enumerate(data_all_channels):
            ch_num = config.acquire_channels[ch_idx]

            n_triggers = len(triggers)
            n_samples = len(triggers[0]["Amplitude (V)"])

            t_axis = triggers[0]["Time (s)"]
            t0 = t_axis[0]
            dt = t_axis[1] - t_axis[0]

            v_set = grp.create_dataset(
                f"ch{ch_num}_v",
                shape=(n_triggers, n_samples),
                dtype="f4",
                compression="gzip",
                chunks=(1, n_samples),
            )
            v_set.attrs["t0"] = t0
            v_set.attrs["dt"] = dt

            for n_trig, trig_data in enumerate(triggers):
                v_set[n_trig, :] = trig_data["Amplitude (V)"]

        self.file.flush()

    def close(self):
        self.file.close()
