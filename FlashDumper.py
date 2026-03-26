from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTreeWidget, QTextEdit, QSplitter, 
                             QToolBar, QStatusBar, QMenu, QToolButton, QSizePolicy, 
                             QFileDialog, QTreeWidgetItem, QFileIconProvider, QLabel, 
                             QMessageBox, QScrollBar)

from PyQt6.QtGui import QAction, QFont
from PyQt6.QtCore import Qt, QFileInfo, QTimer

from sys import exit, argv

import os
import threading

import hexdump

from src.connection import Connection
from src.signals import SerialSignals
from src.dumpWindow import DumpWindow

class UARTManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data reader")
        self.resize(1000, 700)

        # Dark mode
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00; /* Green terminal text */
            }
            QPushButton {
                background-color: #3c3f41;
                border: 1px solid #555;
            }
        """)
		
        self.signals = SerialSignals()
        self.signals.data_received.connect(self.update_terminal)

        self.current_port = None
        self.current_baud = "115200"
        self.hex_mode = False

        self.current_opened_file = None

        self.connection = Connection()

        self.init_toolbar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        self.h_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.v_splitter = QSplitter(Qt.Orientation.Vertical)

        self.icon_provider = QFileIconProvider()

        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabel("Files explorer")

        self.file_tree.itemDoubleClicked.connect(self.on_file_clicked)
        
        self.editor = QTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setPlaceholderText("Hex explorer")

        editor_font = QFont("Courier New", 12) 
        editor_font.setStyleHint(QFont.StyleHint.Monospace)
        self.editor.setFont(editor_font)

        self.editor.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap) # Stop the text from wrapping to the next line

        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setStyleSheet("background-color: #1e1e1e; color: #00ff00;")
        self.terminal.setFont(QFont("Courier New", 10))
        self.terminal.append("--- PLAIN TEXT mode ---")

        # ditor and Terminal to Vertical splitter
        self.v_splitter.addWidget(self.editor)
        self.v_splitter.addWidget(self.terminal)
        self.v_splitter.setStretchFactor(0, 2) 
        self.v_splitter.setStretchFactor(1, 2)

        # Vertical Splitter to Horizontal splitter
        self.h_splitter.addWidget(self.file_tree)
        self.h_splitter.addWidget(self.v_splitter)
        self.h_splitter.setStretchFactor(0, 1)
        self.h_splitter.setStretchFactor(1, 4)

        main_layout.addWidget(self.h_splitter)

        self.status_bar_text("Ready")

    def status_bar_text(self, text):
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage(text)

    def update_terminal(self, data):
        
        if self.hex_mode:
            hex_text = data.hex(' ').upper() + " "
            self.terminal.insertPlainText(hex_text)
        
        else:
            try:
                text = data.decode('ascii', errors='replace')
                self.terminal.insertPlainText(text)
            except Exception:
                self.terminal.insertPlainText("[Decode Error]")

        self.terminal.moveCursor(self.terminal.textCursor().MoveOperation.End)

    def init_toolbar(self):
        toolbar = self.addToolBar("MainToolbar")

        files_btn = QToolButton()
        files_btn.setText("Files")
        files_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        files_menu = QMenu(self)

        files_menu.addSeparator()
        open_file_act = files_menu.addAction("Open file")
        open_dir_act = files_menu.addAction("Open folder")

        open_file_act.triggered.connect(self.open_file)
        open_dir_act.triggered.connect(self.open_folder)

        files_btn.setMenu(files_menu)
        toolbar.addWidget(files_btn)

        device_btn = QToolButton()
        device_btn.setText("Devices")
        device_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        
        device_menu = QMenu(self)
        
        self.port_menu = QMenu("Port", self)
        self.baud_menu = QMenu("Baudrate", self)
        
        device_menu.addMenu(self.port_menu)
        device_menu.addMenu(self.baud_menu)
        
        bauds = ["9600", "115200", "230400", "460800"]
        for b in bauds:
            action = self.baud_menu.addAction(b)
            action.triggered.connect(lambda checked, val=b: self.set_baud(val))
            
        self.refresh_ports()
        
        device_menu.addSeparator()
        refresh_act = device_menu.addAction("Refresh List")
        refresh_act.triggered.connect(self.refresh_ports)

        device_btn.setMenu(device_menu)
        toolbar.addWidget(device_btn)

        toolbar = self.addToolBar("Main")

        self.hex_action = QAction("Hex View", self)
        self.hex_action.setCheckable(True)
        self.hex_action.triggered.connect(self.toggle_hex_mode)
        
        toolbar.addAction(self.hex_action)
    
        #====================================
        #           DUMP WINDOW
        #====================================

        dump_action = QAction("Flash Dump", self)
        dump_action.setStatusTip("Extract firmware from a connected board")
        dump_action.triggered.connect(self.open_dump_window)
        
        toolbar.addAction(dump_action)

        #====================================
        #           CONNECTION BUTTONS
        #====================================

        # DISCONNECT BUTTON
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        toolbar.addWidget(spacer)

        self.disconnect_btn = QToolButton()
        self.disconnect_btn.setText("Disconnect")
        
        self.disconnect_btn.setStyleSheet("""
            QToolButton {
                background-color: #9c1124; 
                color: white; 
                font-weight: bold; 
                border-radius: 4px;
                padding: 5px 15px;
            }
            QToolButton:hover {
                background-color: #b3172c;
            }
            QToolButton:pressed {
                background-color: #9c1124;
            }
        """)

        toolbar.addWidget(self.disconnect_btn)

        if self.connection.is_running:
            self.disconnect_btn.clicked.connect(self.disconnect_click)

        # CONNECT BUTTON
        self.connect_btn = QToolButton()
        self.connect_btn.setText("Connect")
        
        self.connect_btn.setStyleSheet("""
            QToolButton {
                background-color: #2e7d32; 
                color: white; 
                font-weight: bold; 
                border-radius: 4px;
                padding: 5px 15px;
            }
            QToolButton:hover {
                background-color: #388e3c;
            }
            QToolButton:pressed {
                background-color: #1b5e20;
            }
        """)

        if not self.connection.is_running:
            self.connect_btn.clicked.connect(self.connect_click)
        
        toolbar.addWidget(self.connect_btn)

    def on_file_clicked(self, file, column):
        file_path = file.text(0)
        
        parent = file.parent()
        while parent:
            file_path = os.path.join(parent.text(0), file_path)
            parent = parent.parent()
        
        full_path = os.path.join(os.path.dirname(self.base_dir), file_path)

        if os.path.isfile(full_path):
            try:
                with open(full_path, 'rb') as f:
                    raw_data = f.read()
                    
                    hex_text = hexdump.hexdump(raw_data, result='return')
                    
                    self.editor.clear()
                    self.editor.insertPlainText(hex_text)
                    
            except Exception as e:
                self.show_error(f"Error opening file: {e}")

            else:
                self.current_opened_file = file_path

    def open_dump_window(self):
        ports = self.connection.get_available_ports()

        if not ports:
            self.show_error("No ports found")
            return

        dialog = DumpWindow(ports_list=ports, parent=self)
        dialog.exec()

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Binary File", "", "All Files (*);;Binary Files (*.bin);;Python Files (*.py)")            

        if file_path:
            
            try:
                with open(file_path, "rb") as f:
                    self.editor.clear()
                    self.editor.insertPlainText(hexdump.hexdump(f.read(1024 * 64), result='return'))

            except Exception as e:
                self.show_error(f"Error opening file: {e}")

            else:
                self.current_opened_file = file_path
                self.editor.insertPlainText("\n[ Data cropped for example ]")

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        
        if folder_path:
            
            self.base_dir = folder_path
            self.file_tree.setHeaderLabel(self.base_dir)
            self.file_tree.clear()
            
            root_name = os.path.basename(folder_path)
            root_item = QTreeWidgetItem(self.file_tree)
            root_item.setText(0, root_name)
            root_item.setExpanded(True)
            
            self.add_file_nodes(folder_path, root_item) # Populates tree recursively

    def add_file_nodes(self, path, parent_item):
        try:
            for directory in sorted(os.listdir(path)):
                full_path = os.path.join(path, directory)
                
                # Create the file explorer tree item
                item = QTreeWidgetItem(parent_item)
                item.setText(0, directory)

                file_info = QFileInfo(full_path)
                icon = self.icon_provider.icon(file_info)
                item.setIcon(0, icon)
                
                if os.path.isdir(full_path):
                    self.add_file_nodes(full_path, item)
                        
        except PermissionError:
            self.show_error(f"No permission to file {path}")

    def disconnect_click(self):
        self.connection.is_running = False
        self.connection.serial_port = None
        self.status_bar_text("Disconnected from device")
        self.statusBar().setStyleSheet("color: red;")

    def connect_click(self):
        self.connection.connect(self.current_port, self.current_baud)

        if self.connection.is_running:
            self.start_serial_thread()

    def toggle_hex_mode(self, checked):
        self.hex_mode = checked
        self.terminal.clear()
        self.terminal.append(f"--- {'HEX' if checked else 'PLAIN TEXT'} mode ---\n")

    def refresh_ports(self):

        self.port_menu.clear()
        ports = self.connection.get_available_ports()
            
        if not ports:
            self.port_menu.addAction("No Devices Found").setEnabled(False)
        else:
            for p in ports:
                action = self.port_menu.addAction(p)
                action.triggered.connect(lambda checked, val=p: self.set_port(val))

    def set_port(self, port):
        self.current_port = port
        self.status_bar_text(f"{self.current_port}: {self.current_baud}")
        self.statusBar().setStyleSheet("color: #2e7d32; font-weight: bold;")

    def set_baud(self, baud):
        self.current_baud = baud
        self.status_bar_text(f"{self.current_port}: {self.current_baud}")
        self.statusBar().setStyleSheet("color: #2e7d32; font-weight: bold;")

    def start_serial_thread(self):
        self.serial_thread = threading.Thread(
            target=self.connection.read_loop, 
            args=(self.signals.data_received.emit,),
            daemon=True # Dies with app
        )
            
        self.serial_thread.start()
        self.statusBar().showMessage(f"Connected to {self.current_port}")

    def show_error(self, message):
        error = QMessageBox(self)
        error.setIcon(QMessageBox.Icon.Critical)
        error.setWindowTitle("ERROR")
        error.setText(message)
        
        error.setStandardButtons(QMessageBox.StandardButton.Ok)
        error.exec()

if __name__ == "__main__":
    app = QApplication(argv)
    window = UARTManager()
    window.show()

    exit(app.exec())
