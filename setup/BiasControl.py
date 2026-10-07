import time
from CAENpy.CAENDesktopHighVoltagePowerSupply import (
    CAENDesktopHighVoltagePowerSupply,
    OneCAENChannel,
)


class BiasControl:
    def __init__(
        self, port="/dev/ttyACM0", channel=0, current_limit=1e-6, max_voltage=400
    ):
        self.caen_unit = CAENDesktopHighVoltagePowerSupply(port=port)
        self.hv = OneCAENChannel(caen=self.caen_unit, channel_number=channel)
        self.max_voltage = max_voltage
        self.hv.set("MAXV", max_voltage)
        self.hv.current_compliance = current_limit

    def __enter__(self):
        self.hv.output = "on"
        time.sleep(0.5)
        return self

    def __exit__(self, *_):
        self.hv.ramp_voltage(0)
        while abs(self.hv.V_mon) > 1.0:
            time.sleep(0.5)

        self.hv.output = "off"

    def set_voltage(self, volts):
        if abs(volts) > self.max_voltage:
            raise ValueError(f"Voltage {volts} exceeds software safety limit!")
        self.hv.ramp_voltage(volts)

    @property
    def current(self):
        return self.hv.I_mon

    @property
    def voltage(self):
        return self.hv.V_mon
