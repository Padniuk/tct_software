import os
import h5py
from tqdm import tqdm


class H5FileManager:
    @staticmethod
    def split_by_voltage(input_file):
        with h5py.File(input_file, "r") as src:
            metadata = dict(src.attrs)
            voltage_groups = [k for k in src.keys() if k.startswith("voltage_")]

            for v_group in tqdm(voltage_groups, desc="Splitting file"):
                output_filename = f"{os.path.splitext(input_file)[0]}_{v_group}.h5"

                with h5py.File(output_filename, "w") as dst:
                    for k, v in metadata.items():
                        dst.attrs[k] = v

                    src.copy(v_group, dst)
        print(f"Split complete. Created {len(voltage_groups)} files.")

    @staticmethod
    def merge_files(output_file, input_files):
        if not input_files:
            print("No files provided for merging.")
            return

        with h5py.File(output_file, "w") as dst:
            with h5py.File(input_files[0], "r") as first_src:
                for k, v in first_src.attrs.items():
                    dst.attrs[k] = v

            for file_path in tqdm(input_files, desc="Merging files"):
                if not os.path.exists(file_path):
                    print(f"Warning: File {file_path} not found. Skipping.")
                    continue

                with h5py.File(file_path, "r") as src:
                    voltage_groups = [k for k in src.keys() if k.startswith("voltage_")]

                    for v_group in voltage_groups:
                        if v_group in dst:
                            continue

                        src.copy(v_group, dst)

        print(f"Merge complete: {output_file}")
