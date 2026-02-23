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
        device_center_xyz = config.device_center
        x_span = config.x_span
        y_span = config.y_span
        x_step = config.step_xy
        y_step = config.step_xy
        rotation_angle_deg = config.rotation_angle_deg
        readout_pads_to_remove = config.remove_pads

        x = np.linspace(-x_span / 2, x_span / 2, int(x_span / x_step + 1))
        y = np.linspace(-y_span / 2, y_span / 2, int(y_span / y_step + 1))

        xx, yy = np.meshgrid(x, y)

        phi = np.arctan2(yy, xx)
        cos = np.cos(rotation_angle_deg * np.pi / 180 + phi)
        sin = np.sin(rotation_angle_deg * np.pi / 180 + phi)
        rr = (xx**2 + yy**2) ** 0.5
        xx, yy = rr * cos, rr * sin

        xx += device_center_xyz[0]
        yy += device_center_xyz[1]
        zz = xx * 0 + device_center_xyz[2]

        remove_these = np.full(xx.shape, False)
        if isinstance(readout_pads_to_remove, dict):
            pitch = readout_pads_to_remove["pitch"]
            size = readout_pads_to_remove["size"]
            if readout_pads_to_remove["shape"] != "square":
                raise ValueError("Only implemented for square pads. ")
            for row in [-1, 1]:
                for col in [-1, 1]:
                    remove_these |= (
                        (xx - device_center_xyz[0] > (col * pitch - size) / 2)
                        & (xx - device_center_xyz[0] < (col * pitch + size) / 2)
                        & (yy - device_center_xyz[1] > (row * pitch - size) / 2)
                        & (yy - device_center_xyz[1] < (row * pitch + size) / 2)
                    )

        positions = [
            [
                (
                    (xx[nx, ny], yy[nx, ny], zz[nx, ny])
                    if remove_these[nx, ny] == False
                    else None
                )
                for ny in range(len(xx[nx]))
            ]
            for nx in range(len(xx))
        ]

        flat_positions = []
        for row in positions:
            for pos in row:
                if pos is not None:
                    flat_positions.append(pos)

        return flat_positions
