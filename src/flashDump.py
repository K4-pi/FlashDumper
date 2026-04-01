from pyocd.core import exceptions

from pyocd.target.pack.pack_target import PackTargets, ManagedPacks

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


class ArmDump():
    def __init__(self, target: str, address, size, output_file):
        self.target = target.upper()
        self.address = address
        self.size = size
        self.output_file = output_file

    def dump(self):
        try:
            with ConnectHelper.session_with_chosen_probe(target_override=self.target) as session:
                target = session.target
            
                target.halt()
                
                FLASH_START = self.address #0x08000000
                FLASH_SIZE  = self.size #0x80000  # 512KB flash
                
                firmware = target.read_memory_block8(FLASH_START, FLASH_SIZE)
                
                with open(self.output_file, 'wb') as f:
                    f.write(bytes(firmware))
                
                print(f"Dumped {len(firmware)} bytes")
                target.resume()

        except exceptions.TargetSupportError:
            print("[*] Pack not found, installing...")
            ManagedPacks.install_pack_by_target(self.target)
            print("[*] Retry now")
        
