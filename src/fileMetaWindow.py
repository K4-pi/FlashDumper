from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QLineEdit, QPushButton, QStackedWidget, 
                             QWidget, QMessageBox, QTreeWidget, QTreeWidgetItem)

class FileMetaWindow(QDialog):
    def __init__(self, meta_data, parent=None):
        super().__init__(parent)

        self.setWindowTitle("File signatures")
        self.setFixedSize(550, 300)

        self.signs_tree = QTreeWidget()
        self.signs_tree.setHeaderLabels(["Property", "Value"])

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)

        layout = QVBoxLayout()
        layout.addWidget(self.signs_tree)
        layout.addWidget(self.close_button)
        
        self.setLayout(layout)

        from time import localtime

        mtime = localtime(meta_data.st_mtime)
        ctime = localtime(meta_data.st_ctime)
        atime = localtime(meta_data.st_atime)

        self.labels = {
            "Protection bits":        meta_data.st_mode,      
            "Inode number":           meta_data.st_ino,      
            "Device":                 meta_data.st_dev,      
            "Number of hard links":   meta_data.st_nlink,      
            "User ID":                meta_data.st_uid,      
            "Group ID":               meta_data.st_gid,      
            "file size (bytes)":   meta_data.st_size,      
            "Last access time":       f"{atime.tm_hour}:{atime.tm_min}:{atime.tm_sec} | {atime.tm_mday}-{atime.tm_mon}-{atime.tm_year}",      
            "Last modification time": f"{mtime.tm_hour}:{mtime.tm_min}:{mtime.tm_sec} | {mtime.tm_mday}-{mtime.tm_mon}-{mtime.tm_year}",      
            "Last metadata change":   f"{ctime.tm_hour}:{ctime.tm_min}:{ctime.tm_sec} | {ctime.tm_mday}-{ctime.tm_mon}-{ctime.tm_year}"      
        }

        keys = self.labels.keys()

        for k in keys:
            item = QTreeWidgetItem([k, str(self.labels[k])])
            self.signs_tree.addTopLevelItem(item)