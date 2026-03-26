from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QLineEdit, QPushButton, QStackedWidget, QWidget)

from os import getcwd

from src.flashDump import Esp32Dump

class DumpWindow(QDialog):
    def __init__(self, ports_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Firmware flash dump")
        self.setFixedSize(450, 400) # not resizable
        
        self.ports = ports_list

        layout = QVBoxLayout(self)

        self.stack = QStackedWidget()
        
        self.stack.addWidget(self.create_esp32_page())
        # self.stack.addWidget(self.create_arm_page())

        layout.addWidget(QLabel("Select Board:"))
        self.board_type = QComboBox()
        self.board_type.addItems(["ESP32 (Serial/UART)", "ARM Cortex-M (SWD/ST-Link)"])
        self.board_type.currentIndexChanged.connect(self.stack.setCurrentIndex)
        layout.addWidget(self.board_type)

        layout.addWidget(self.stack)

        btn_layout = QHBoxLayout()
        self.dump_btn = QPushButton("Dump")
        self.dump_btn.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        self.dump_btn.clicked.connect(self.run_dumping)
        
        btn_layout.addWidget(self.dump_btn)
        layout.addLayout(btn_layout)

    def create_esp32_page(self):
        page = QWidget()
        l = QVBoxLayout(page)
        
        self.port_selector = QComboBox()
        
        if not self.ports:
            self.port_selector.addItem("No Devices Detected")
            self.port_selector.setEnabled(False)
        else:
            self.port_selector.addItems(self.ports)
            
        l.addWidget(QLabel("Select ESP32 Port:"))
        l.addWidget(self.port_selector)

        l.addWidget(QLabel("Baud Rate:"))
        self.esp_baud = QComboBox()
        self.esp_baud.addItems(["115200", "460800", "921600"])
        l.addWidget(self.esp_baud)
        
        l.addWidget(QLabel("Flash size (Bytes):"))
        self.esp_flash_size = QLineEdit("0x400000")
        l.addWidget(self.esp_flash_size)

        l.addWidget(QLabel("File path:"))
        self.save_path = QLineEdit(str(getcwd()) + "/_dump.bin")
        l.addWidget(self.save_path)
        
        return page

    # def create_arm_page(self):
    #     page = QWidget()
    #     l = QVBoxLayout(page)
    #     l.addWidget(QLabel("Target Chip (e.g. stm32f103c8):"))
    #     self.arm_target = QLineEdit("stm32f103c8")
    #     l.addWidget(self.arm_target)
        
    #     l.addWidget(QLabel("Memory Address (Start):"))
    #     self.arm_addr = QLineEdit("0x08000000")
    #     l.addWidget(self.arm_addr)
        
    #     l.addWidget(QLabel("Size (Bytes):"))
    #     self.arm_size = QLineEdit("0x10000") # 64KB
    #     l.addWidget(self.arm_size)
    #     return page

    def run_dumping(self):

        index = self.board_type.currentIndex()

        if index == 0: # ESP32
            print(f"Starting dump for ESP32 in {self.save_path}")
            esp = Esp32Dump(self.esp_baud.currentText(), self.port_selector.currentText(), self.save_path, self.esp_flash_size)
            esp.dump()

        elif index == 1: # ARM
            print("ARM")

        self.accept()