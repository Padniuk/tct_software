from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot


class VoltageWorker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, bias):
        super().__init__()
        self.bias = bias

    @pyqtSlot(float)
    def change_voltage(self, val):
        try:
            self.bias.set_voltage(val)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()
