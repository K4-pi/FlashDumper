import serial
import serial.tools.list_ports
import threading

class Connection:
    def __init__(self):
        self.serial_port = None
        self.baudrate = 0
        self.is_running = False

    def get_available_ports(self):
        return [port.device for port in serial.tools.list_ports.comports()]

    def connect(self, port, baudrate=115200):
        try:
            self.baudrate = baudrate

            self.serial_port = serial.Serial(port, baudrate, timeout=1, rtscts=True)

            self.is_running = True

        except Exception as e:
            print(f"Connection Error: {e}")

        else:
            print(f"Connected to {port}: {baudrate}")

    def send_command(self, cmd):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write((cmd + '\r\n').encode('utf-8'))

    def read_loop(self, callback):
        while self.is_running:
            if self.serial_port.in_waiting > 0:
                data = self.serial_port.read(self.serial_port.in_waiting)

                callback(data)
