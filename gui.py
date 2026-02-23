import sys
from gui import Ui
from configs import config
from PyQt6.QtWidgets import QApplication
from setup import TCTControl, BiasControl, LeCroyControl

if __name__ == "__main__":
    app = QApplication(sys.argv)

    scope = LeCroyControl()
    bias = BiasControl(
        port="/dev/ttyACM0", current_limit=config.current_compliance_amperes
    )
    tct = TCTControl(dac=config.laser_dac, frequency=config.laser_frequency)

    with bias as hv, tct as laser:
        ui = Ui(hv, laser, scope)

        sys.exit(app.exec())
