import sys
import os
import time
import stat
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QTextEdit
)
from PyQt6.QtCore import Qt


class FileMetadataViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Metadata Viewer")
        self.setMinimumSize(600, 450)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # File selection row
        sel_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Enter file path or click Browse...")
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_file)
        sel_layout.addWidget(self.file_path_edit)
        sel_layout.addWidget(browse_btn)
        layout.addLayout(sel_layout)

        # Show metadata button
        self.show_btn = QPushButton("Show Metadata")
        self.show_btn.clicked.connect(self.show_metadata)
        layout.addWidget(self.show_btn)

        # Output area
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            self.file_path_edit.setText(file_path)

    def show_metadata(self):
        file_path = self.file_path_edit.text().strip()
        if not file_path:
            self.output_text.setText("❌ Please enter a file path.")
            return

        path = Path(file_path)
        if not path.exists():
            self.output_text.setText(f"❌ File not found:\n{file_path}")
            return

        try:
            stat_info = path.stat()
            output = []

            output.append(f"📄 File: {path.absolute()}")
            output.append("-" * 60)

            # Size
            size_bytes = stat_info.st_size
            size_kb = size_bytes / 1024
            size_mb = size_kb / 1024
            output.append(f"📏 Size: {size_bytes} bytes ({size_kb:.2f} KB / {size_mb:.2f} MB)")

            # Type
            if path.is_dir():
                output.append("📁 Type: Directory")
            elif path.is_file():
                output.append("📄 Type: Regular file")
            else:
                output.append("❓ Type: Special (symlink, etc.)")

            # Timestamps
            atime = time.ctime(stat_info.st_atime)
            mtime = time.ctime(stat_info.st_mtime)
            ctime = time.ctime(stat_info.st_ctime)
            output.append(f"🕒 Last access (atime): {atime}")
            output.append(f"✏️ Last content modification (mtime): {mtime}")
            output.append(f"⚙️ Last metadata change (ctime): {ctime}")

            # Permissions (Unix-like)
            mode = stat_info.st_mode
            perms = stat.filemode(mode)
            output.append(f"🔐 Permissions: {perms}")

            # Owner (Unix only)
            try:
                uid = stat_info.st_uid
                gid = stat_info.st_gid
                output.append(f"👤 Owner (UID): {uid}  (GID): {gid}")
            except AttributeError:
                pass

            # Hard links
            output.append(f"🔗 Hard link count: {stat_info.st_nlink}")

            # Extension (if file)
            if path.is_file():
                ext = path.suffix if path.suffix else "none"
                output.append(f"🔖 Extension: {ext}")

            output.append("-" * 60)

            self.output_text.setText("\n".join(output))

        except Exception as e:
            self.output_text.setText(f"⚠️ Error reading metadata:\n{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileMetadataViewer()
    window.show()
    sys.exit(app.exec())
