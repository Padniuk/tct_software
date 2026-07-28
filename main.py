import os
import tqdm
import datetime
import traceback
from configs import config
from utils import DataWriter, setup_logging
from tools import analyse_waveforms, save_analysis
from setup import TCTControl, BiasControl, LeCroyControl


def main():
    dut_path = os.path.join(config.output_folder, config.wafer_type, config.dut_name)

    if not os.path.exists(dut_path):
        os.makedirs(dut_path)

    log = setup_logging(dut_path, config.logging_level)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    h5_filename = os.path.join(dut_path, f"{config.dut_name}.h5")

    if os.path.exists(h5_filename):
        user_input = (
            input(
                f"WARNING: Data file '{h5_filename}' already exists. Overwrite? (y/n): "
            )
            .strip()
            .lower()
        )
        if user_input != "y":
            log.info("Scan cancelled by user to prevent overwriting existing data.")
            return

    writer = DataWriter(
        h5_filename,
        {
            "dut_name": config.dut_name,
            "wafer_type": config.wafer_type,
            "laser_dac": config.laser_dac,
            "laser_frequency": config.laser_frequency,
            "orientation": config.orientation,
            "step_size_u": config.step_u,
            "step_size_v": config.step_v,
            "timestamp": timestamp,
        },
    )

    tct = TCTControl(dac=config.laser_dac, frequency=config.laser_frequency)
    positions = tct.create_list_of_positions()
    bias = BiasControl(
        port="/dev/ttyACM0", current_limit=config.current_compliance_amperes
    )
    scope = LeCroyControl()

    log.info(f"Starting run for DUT: {config.dut_name}")

    try:
        with bias as hv, tct as laser:
            scope.configure_for_double_pulse(
                trigger_delay=-1e-9 * config.trigger_delay_scope
            )
            scope.set_sequence_mode(num_segments=config.n_triggers_per_position)

            for voltage in config.voltages:
                log.info(f"--- Voltage Step: {voltage}V ---")
                hv.set_voltage(voltage)
                log.info(f"Voltage was applied successfully")

                current_val = hv.current
                log.info(f"Bias current: {current_val*1e9:.2f} nA")

                for n_pos_count, target_pos in enumerate(
                    tqdm.tqdm(positions, desc=f"{voltage}V Scan")
                ):
                    laser.stages.move_to(
                        x=target_pos[0], y=target_pos[1], z=target_pos[2]
                    )
                    actual_pos = laser.stages.position

                    scope.acquire_sequence(timeout=config.oscilloscope_timeout)

                    data_all_channels = []

                    for n_channel in config.acquire_channels:
                        batch_waveforms = scope.get_waveforms(channel=n_channel)
                        data_all_channels.append(batch_waveforms)

                    writer.write_position(
                        voltage=voltage,
                        current=current_val,
                        n_pos=n_pos_count,
                        actual_pos=actual_pos,
                        data_all_channels=data_all_channels,
                    )

    except KeyboardInterrupt:
        log.warning("User interrupted the scan. Safe shutdown initiated...")
    except Exception as e:
        log.error(f"Unexpected Error: {e}")
        log.debug(f"Full Traceback:\n{traceback.format_exc()}")
    finally:
        writer.close()
        log.info("The run is finished. All hardware returned to safe state.")

    log.info("Preprocessing waveforms")
    for voltage in config.voltages:
        df = analyse_waveforms(f"{dut_path}/{config.dut_name}.h5", voltage)
        save_analysis(df, f"{dut_path}/{config.dut_name}_{int(voltage)}V.csv")
    log.info("Waveforms analysis was done")


if __name__ == "__main__":
    main()
