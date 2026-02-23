from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot


class ScopeWorker(QObject):
    data_ready = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, scope, n_channels):
        super().__init__()
        self.scope = scope
        self.n_channels = n_channels
        self.running = True

    @pyqtSlot()
    def loop_capture(self):
        while self.running:
            try:
                data = []
                for channel in range(1, self.n_channels + 1):
                    data.append(self.scope.get_waveforms(channel=channel))

                if data:
                    self.data_ready.emit(data)
            except Exception as e:
                self.error.emit(str(e))

            QThread.msleep(50)
