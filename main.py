from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTreeWidget, QTextEdit, QSplitter, 
                             QToolBar, QStatusBar, QMenu, QToolButton, QSizePolicy, 
                             QFileDialog, QTreeWidgetItem, QFileIconProvider, QLabel, 
                             QMessageBox, QScrollBar, QHeaderView, QAbstractItemView,
                             QInputDialog, QLineEdit)

from PyQt6.QtGui import QAction, QFont
from PyQt6.QtCore import Qt, QFileInfo, QTimer

from sys import exit, argv

import os
import threading

import hexdump

from src.connection import Connection
from src.signals import SerialSignals
from src.dumpWindow import DumpWindow
from src.fileMetaWindow import FileMetaWindow

from src.analizeFile import strings, analyze_file_meta

class UARTManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data reader")
        self.resize(1300, 800)

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

        self.strings_tree = QTreeWidget()
        self.strings_tree.setHeaderLabel("Strings")

        self.editor_tree = QTreeWidget()
        self.editor_tree.setHeaderLabel("Editor")

        self.editor_tree.setColumnCount(3)
        self.editor_tree.setHeaderLabels(["Address", "Hex Content", "ASCII"])

        self.editor_tree.header().setMinimumSectionSize(125)

        self.editor_tree.header().setStretchLastSection(False)

        self.editor_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.editor_tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
       
        self.editor_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        self.editor_tree.setColumnWidth(0, 125)
        self.editor_tree.setColumnWidth(1, 475)
        self.editor_tree.setColumnWidth(2, 175)

        self.editor_tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.editor_tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self.editor_tree.itemDoubleClicked.connect(self.content_item_clicked)

        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setStyleSheet("background-color: #1e1e1e; color: #00ff00;")
        self.terminal.setFont(QFont("Courier New", 10))
        self.terminal.append("--- PLAIN TEXT mode ---")

        # ditor and Terminal to Vertical splitter
        self.v_splitter.addWidget(self.editor_tree)
        self.v_splitter.addWidget(self.terminal)
        self.v_splitter.setStretchFactor(0, 3)
        self.v_splitter.setStretchFactor(1, 1)

        # Vertical Splitter to Horizontal splitter
        self.h_splitter.addWidget(self.file_tree)
        self.h_splitter.addWidget(self.v_splitter)
        self.h_splitter.setStretchFactor(0, 1)
        self.h_splitter.setStretchFactor(1, 4)
        self.h_splitter.addWidget(self.strings_tree)

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
        save_file_act = files_menu.addAction("Save file")
        
        save_file_act.triggered.connect(self.save_content_to_file)
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
        #           META WINDOW
        #====================================

        meta_action = QAction("Signatures", self)
        meta_action.setStatusTip("Show signatures of loaded file")
        meta_action.triggered.connect(self.open_meta_window)

        toolbar.addAction(meta_action)

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
    
    def content_item_clicked(self, item, column):
        item_text = item.text(column)
        value = self.edit_window(item_text)

        if value:
            item.setText(column, value)

            s = []

            for b in bytes.fromhex(value):    
                s.append(chr(b) if 32 <= b < 127 else '.')

            item.setText(2, "".join(s)) 

    def on_file_clicked(self, file, column):
        file_path = file.text(0)
        
        parent = file.parent()
        while parent:
            file_path = os.path.join(parent.text(0), file_path)
            parent = parent.parent()
        
        full_path = os.path.join(os.path.dirname(self.base_dir), file_path)

        if os.path.isfile(full_path):
            self.open_file(full_path)

    def open_meta_window(self):

        if self.current_opened_file is None:
            return

        meta_data = analyze_file_meta(self.current_opened_file)
        dialog = FileMetaWindow(meta_data, self)
        dialog.exec()

    def open_dump_window(self):
        ports = self.connection.get_available_ports()

        if not ports:
            self.show_error("No ports found")
            return

        dialog = DumpWindow(ports_list=ports, parent=self)
        dialog.exec()

    def open_file(self, filename=None):

        print(f"filename = {filename}")

        if filename:
            file_path = filename
        
        else:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open Binary File", "", "All Files (*);;Binary Files (*.bin);;Python Files (*.py)")            
        
        if file_path:
            
            try:
                with open(file_path, "rb") as f:
                    # hex_data = f.read(2048 * 64)
                    hex_data = f.read()

                    self.editor_tree.clear()

                    for line in hexdump.hexdump(hex_data, result='generator'):
                        address = line[:10].strip()
                        content = line[10:59].strip().replace("  ", " ")
                        text = line[60:].strip() 

                        editor_item = QTreeWidgetItem(self.editor_tree)
                        
                        editor_item.setText(0, address)
                        editor_item.setText(1, content)
                        editor_item.setText(2, text)
                        
                        editor_item.setFlags(editor_item.flags() | Qt.ItemFlag.ItemIsSelectable)
                        
                        font = QFont("Courier New", 12)
                        for i in range(3):
                            editor_item.setFont(i, font)

                    self.strings_tree.clear()

                    # STRINGS
                    for s in strings(file_path, 4):
                        string_item = QTreeWidgetItem(self.strings_tree)
                        string_item.setText(0, s.decode('utf-8'))
                        string_item.setExpanded(True)

            except Exception as e:
                self.show_error(f"Error opening file: {e}")

            else:
                self.current_opened_file = file_path

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

    def save_content_to_file(self):
        try: 
            with open(self.current_opened_file, "wb") as f:
                for i in range(self.editor_tree.topLevelItemCount()):
                    item = self.editor_tree.topLevelItem(i)
                    text = item.text(1)
                    f.write(bytes.fromhex(text))

        except Exception as ex:
            self.show_error(f"SAVE FILE ERROR: {ex}")

        else:
            print("saved file")

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

    def edit_window(self, data):
        
        new_text, ok = QInputDialog.getText(
            self, 
            "Edit", 
            f"{data}\n\nEdit:", 
            QLineEdit.EchoMode.Normal, 
            data
        )

        if ok and new_text:
            print(f"Zaktualizowano: {new_text}")
            return new_text
        
        return None

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
