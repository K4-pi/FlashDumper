from PyQt6.QtCore import QObject, pyqtSignal

class SerialSignals(QObject):
    data_received = pyqtSignal(bytes)