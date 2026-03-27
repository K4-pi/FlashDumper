from pyocd.core.helpers import ConnectHelper
import esptool

class Esp32Dump():
    def __init__(self, baudrate, port, output_file, flash_size=0x400000):
        self.baudrate = baudrate
        self.port = port
        self.flash_size = flash_size # 0x400000 4MB
        self.output_file = output_file # 'dump.bin'

        self.command = ['--port', str(self.port), '--baud', str(self.baudrate), 'read_flash', '0', str(self.flash_size), str(self.output_file)]

    def dump(self):

        try:
            esptool.main(self.command)
        except Exception as e:
            print(f"ESP32 DUMP ERROR: {e}")


# class ArmDump():

    