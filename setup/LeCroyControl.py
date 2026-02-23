import TeledyneLeCroyPy


class LeCroyControl:
    def __init__(self, address="USB0::0x05ff::0x1023::4751N40408::INSTR"):
        self.scope = TeledyneLeCroyPy.LeCroyWaveRunner(address)
        self.is_sequence_mode = False

    def configure_for_double_pulse(self, trigger_delay=-30e-9):
        self.scope.set_trig_source("ext")
        self.scope.set_trig_level("ext", -175e-3)  # Totally empiric
        self.scope.set_trig_coupling("ext", "DC")
        self.scope.set_trig_slope("ext", "negative")
        self.scope.set_tdiv("20ns")
        self.scope.set_trig_delay(trigger_delay)

    def set_sequence_mode(self, num_segments):
        if num_segments <= 1:
            self.scope.sampling_mode_sequence("off")
            self.is_sequence_mode = False
        else:
            self.scope.sampling_mode_sequence("on", number_of_segments=num_segments)
            self.is_sequence_mode = True

    def acquire_sequence(self, timeout=5):
        self.scope.wait_for_single_trigger(timeout=timeout)

    def get_waveforms(self, channel):
        raw_data = self.scope.get_waveform(n_channel=channel)
        waveforms = raw_data["waveforms"]
        return waveforms
