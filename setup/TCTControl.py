import numpy as np
import PyticularsTCT
from configs import config
from PyticularsTCT.find_ximc_stages import map_coordinates_to_serial_ports


class TCTControl(PyticularsTCT.TCT):
    def __init__(self, dac, frequency):
        stages_coordinates = {"00003A48": "x", "00003A57": "y", "000038CE": "z"}
        ports = map_coordinates_to_serial_ports(stages_coordinates)

        super().__init__(
            x_stage_port=ports["x"], y_stage_port=ports["y"], z_stage_port=ports["z"]
        )

        self.laser.frequency = frequency
        self.laser.DAC = int(dac)

    def update_laser(self, frequency, dac):
        self.laser.off()
        self.laser.frequency = frequency
        self.laser.DAC = int(dac)

    def __enter__(self):
        self.laser.on()
        return self

    def __exit__(self, *_):
        self.laser.off()

    def create_list_of_positions(self):
        device_center_xyz = np.array(config.device_center)
        u_span = config.u_span
        v_span = config.v_span
        u_step = config.step_u
        v_step = config.step_v
        rotation_angle_deg = config.rotation_angle_deg
        readout_pads_to_remove = config.remove_pads

        orientation = getattr(config, "orientation", "xy").lower().strip()

        u_coords = np.linspace(-u_span / 2, u_span / 2, int(u_span / u_step + 1))
        v_coords = np.linspace(-v_span / 2, v_span / 2, int(v_span / v_step + 1))
        uu, vv = np.meshgrid(u_coords, v_coords)

        phi = np.arctan2(vv, uu)
        rr = np.sqrt(uu**2 + vv**2)
        rad = np.deg2rad(rotation_angle_deg)
        uu, vv = rr * np.cos(rad + phi), rr * np.sin(rad + phi)

        axis_map = {"x": 0, "y": 1, "z": 2}

        if len(orientation) != 2 or not all(c in axis_map for c in orientation):
            raise ValueError(
                f"Invalid orientation '{orientation}'. Use combinations of 'x', 'y', 'z' (e.g., 'xy', 'yx', 'xz')."
            )

        coords = np.tile(device_center_xyz, (uu.shape[0], uu.shape[1], 1))

        u_axis_idx = axis_map[orientation[0]]
        v_axis_idx = axis_map[orientation[1]]

        coords[:, :, u_axis_idx] += uu
        coords[:, :, v_axis_idx] += vv

        remove_these = np.full(uu.shape, False)
        if isinstance(readout_pads_to_remove, dict):
            pitch = readout_pads_to_remove["pitch"]
            size = readout_pads_to_remove["size"]
            if readout_pads_to_remove["shape"] != "square":
                raise ValueError("Only implemented for square pads.")

            for row in [-1, 1]:
                for col in [-1, 1]:
                    remove_these |= (
                        (uu > (col * pitch - size) / 2)
                        & (uu < (col * pitch + size) / 2)
                        & (vv > (row * pitch - size) / 2)
                        & (vv < (row * pitch + size) / 2)
                    )

        flat_positions = []
        for r in range(uu.shape[0]):
            for c in range(uu.shape[1]):
                if not remove_these[r, c]:
                    flat_positions.append(tuple(coords[r, c]))

        return flat_positions
