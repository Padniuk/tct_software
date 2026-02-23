from PyQt6 import uic
import pyqtgraph as pg
from gui.workers import VoltageWorker, ScopeWorker
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout
from PyQt6.QtCore import QTimer, QThread, pyqtSignal, pyqtSlot


class Ui(QMainWindow):
    operate_voltage_signal = pyqtSignal(float)

    def __init__(self, bias, tct, scope):
        super().__init__()
        self.bias = bias
        self.tct = tct
        self.scope = scope

        uic.loadUi("gui/main_window.ui", self)
        self.setWindowTitle("TCT gui")

        self.scope.configure_for_double_pulse(trigger_delay=-30e-9)
        self.scope.set_sequence_mode(1)

        self.step_xy.setText("10")
        self.step_z.setText("10")

        self.laser_dac.setText("500")
        self.laser_frequency.setText("1000")

        self.update_position_labels()

        self.go_to_position.clicked.connect(self.move_to_position)

        self.xy_up.clicked.connect(lambda: self.xy_shift_to_position(self.xy_up))
        self.xy_down.clicked.connect(lambda: self.xy_shift_to_position(self.xy_down))
        self.xy_right.clicked.connect(lambda: self.xy_shift_to_position(self.xy_right))
        self.xy_left.clicked.connect(lambda: self.xy_shift_to_position(self.xy_left))

        # voltage_status and power_off button - remove
        self.plot_view = pg.PlotWidget()

        pg.setConfigOptions(antialias=False)

        self.plot_view.setBackground("k")
        self.plot_view.showGrid(x=True, y=True, alpha=0.3)
        self.plot_view.setYRange(-0.1, 0.05, padding=0)

        self.curves = []
        for color in ["y", "m", "c", "g"]:
            self.curves.append(self.plot_view.plot(pen=pg.mkPen(color, width=1)))

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot_view)

        self.waveforms_graph.setLayout(layout)

        self.scope_thread = QThread()
        self.scope_worker = ScopeWorker(self.scope, len(self.curves))
        self.scope_worker.moveToThread(self.scope_thread)
        self.scope_worker.data_ready.connect(self.update_waveforms_plot)
        self.scope_thread.started.connect(self.scope_worker.loop_capture)

        self.scope_thread.start()

        self.hv_timer = QTimer()
        self.hv_timer.timeout.connect(self.track_voltage_supply)
        self.hv_timer.start(500)

        self.desire_voltage.setText("0")
        self.voltage_thread = QThread()
        self.voltage_worker = VoltageWorker(self.bias)
        self.voltage_worker.moveToThread(self.voltage_thread)
        self.operate_voltage_signal.connect(self.voltage_worker.change_voltage)
        self.voltage_worker.finished.connect(self.on_voltage_ramp_finished)
        self.voltage_worker.error.connect(lambda err: self.statusbar.showMessage(err))

        self.voltage_thread.start()

        self.update_voltage.clicked.connect(self.change_voltage)
        self.laser_switch.clicked.connect(self.switch_laser)

        self.show()

    def update_waveforms_plot(self, data):
        if data is not None:
            for i, curve in enumerate(self.curves):
                segment = data[i][0]
                x = segment["Time (s)"]
                y = segment["Amplitude (V)"]
                curve.setData(x, y)

    def move_to_position(self):
        x = 1e-6 * float(self.x_position.text())
        y = 1e-6 * float(self.y_position.text())
        z = 1e-6 * float(self.z_position.text())
        self.tct.stages.move_to(x=x, y=y, z=z)
        self.statusbar.showMessage(
            f"Moved to x={round(1e6*x,3)} y={round(1e6*y,3)} z={round(1e6*z,3)}"
        )

    def xy_shift_to_position(self, button):
        step = 1e-6 * int(self.step_xy.text())
        if button == self.xy_up:
            self.tct.stages.move_rel(y=step)
        elif button == self.xy_down:
            self.tct.stages.move_rel(y=-step)
        elif button == self.xy_right:
            self.tct.stages.move_rel(x=step)
        elif button == self.xy_left:
            self.tct.stages.move_rel(x=-step)

        self.update_position_labels()
        self.statusbar.showMessage(
            f"Went by {self.step_xy.text()} in {button.text()} direction of XY"
        )

    def z_shift_to_position(self, button):
        step = 1e-6 * int(self.step_z.text())
        if button == self.z_up:
            self.tct.stages.move_rel(z=step)
        elif button == self.z_down:
            self.tct.stages.move_rel(z=-step)

        self.update_position_labels()
        self.statusbar.showMessage(
            f"Went by {self.step_z.text()} in {button.text()} direction of Z"
        )

    def update_position_labels(self):
        x, y, z = self.tct.stages.position
        self.x_position.setText(f"{round(1e6*x,3)}")
        self.y_position.setText(f"{round(1e6*y,3)}")
        self.z_position.setText(f"{round(1e6*z,3)}")

    def change_voltage(self):
        target_val = float(self.desire_voltage.text())
        self.update_voltage.setEnabled(False)
        self.desire_voltage.setEnabled(False)
        self.operate_voltage_signal.emit(target_val)

    def on_voltage_ramp_finished(self):
        self.update_voltage.setEnabled(True)
        self.desire_voltage.setEnabled(True)

    def track_voltage_supply(self):
        self.current_now.setText(f"{round(1e9*self.bias.current,3)} nA")
        self.voltage_now.setText(f"{round(self.bias.voltage,1)} V")

    def switch_laser(self):
        if self.laser_switch.text() == "On":
            self.tct.update_laser(
                float(self.laser_frequency.text()), float(self.laser_dac.text())
            )
            self.tct.__enter__()
            self.laser_status.setText("On")
            self.laser_switch.setText("Off")
        else:
            self.tct.__exit__()
            self.laser_status.setText("Off")
            self.laser_switch.setText("On")

    def closeEvent(self, event):
        self.scope_worker.running = False
        self.scope_thread.quit()
        self.scope_thread.wait()

        self.voltage_thread.quit()
        self.voltage_thread.wait()
        super().closeEvent(event)
