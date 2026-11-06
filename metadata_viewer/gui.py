from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QLineEdit, QFileDialog, QScrollArea, QFrame, 
    QApplication, QMessageBox, QSizePolicy, QToolButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QThread, pyqtSlot, QMimeData
from PyQt6.QtGui import QIcon, QFont, QColor, QPalette, QPixmap, QGuiApplication

from metadata_viewer.extractor import MetadataExtractor
from metadata_viewer.utils import export_to_json, export_to_csv
from pathlib import Path

class Worker(QThread):
    """Worker thread to prevent UI freezing during metadata extraction."""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, path: str):
        super().__init__()
        self.path = path

    def run(self):
        try:
            data = MetadataExtractor.extract_all(Path(self.path))
            self.finished.emit(data)
        except Exception as e:
            self.error.emit(str(e))

class MetadataCard(QFrame):
    """A modern card to display a group of metadata fields."""
    def __init__(self, title: str, data: dict):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName("MetadataCard")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)

        # Title
        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setObjectName("Divider")
        layout.addWidget(line)

        # Data pairs
        for key, value in data.items():
            row_widget = QWidget()
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(0, 2, 0, 2)
            row.setSpacing(10)
            
            key_label = QLabel(key)
            key_label.setObjectName("KeyLabel")
            
            val_label = QLabel(str(value))
            val_label.setObjectName("ValueLabel")
            val_label.setWordWrap(True)
            val_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            val_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            
            copy_btn = QToolButton()
            copy_btn.setText("📋")
            copy_btn.setToolTip(f"Copy {key}")
            copy_btn.setObjectName("CopyButton")
            copy_btn.clicked.connect(lambda checked, v=value: self.copy_to_clipboard(str(v)))
            
            row.addWidget(key_label)
            row.addStretch()
            row.addWidget(val_label)
            row.addWidget(copy_btn)
            
            layout.addWidget(row_widget)

    def copy_to_clipboard(self, text):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)

class ModernMetadataViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Metadata Viewer")
        self.setMinimumSize(1000, 800)
        self.current_data = None
        self.current_path = None
        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)

        # Top Action Bar
        action_bar = QFrame()
        action_bar.setObjectName("ActionBar")
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(15, 15, 15, 15)
        action_layout.setSpacing(15)

        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Drag and drop a file here or browse...")
        self.file_path_edit.setObjectName("PathEdit")
        
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setObjectName("PrimaryButton")
        self.browse_btn.clicked.connect(self.browse_file)

        self.extract_btn = QPushButton("View Metadata")
        self.extract_btn.setObjectName("SecondaryButton")
        self.extract_btn.clicked.connect(self.start_extraction)

        action_layout.addWidget(self.file_path_edit)
        action_layout.addWidget(self.browse_btn)
        action_layout.addWidget(self.extract_btn)
        
        main_layout.addWidget(action_bar)

        # Secondary toolbar (Export / Search)
        self.toolbar = QWidget()
        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search metadata...")
        self.search_edit.setObjectName("SearchEdit")
        self.search_edit.textChanged.connect(self.filter_metadata)
        
        self.export_json_btn = QPushButton("Export JSON")
        self.export_json_btn.setObjectName("ToolbarButton")
        self.export_json_btn.clicked.connect(self.export_json)
        self.export_json_btn.setEnabled(False)

        self.export_csv_btn = QPushButton("Export CSV")
        self.export_csv_btn.setObjectName("ToolbarButton")
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_csv_btn.setEnabled(False)

        self.copy_all_btn = QPushButton("Copy All")
        self.copy_all_btn.setObjectName("ToolbarButton")
        self.copy_all_btn.clicked.connect(self.copy_all)
        self.copy_all_btn.setEnabled(False)

        toolbar_layout.addWidget(self.search_edit)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.copy_all_btn)
        toolbar_layout.addWidget(self.export_json_btn)
        toolbar_layout.addWidget(self.export_csv_btn)
        
        main_layout.addWidget(self.toolbar)

        # Split view for Preview and Metadata
        content_split = QHBoxLayout()
        
        # Left side: Preview
        self.preview_panel = QFrame()
        self.preview_panel.setObjectName("PreviewPanel")
        self.preview_panel.setFixedWidth(300)
        self.preview_panel.hide()
        preview_layout = QVBoxLayout(self.preview_panel)
        
        self.preview_label = QLabel("Preview")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setObjectName("PreviewLabel")
        preview_layout.addWidget(self.preview_label)
        
        self.image_preview = QLabel()
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setMinimumSize(250, 250)
        self.image_preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        preview_layout.addWidget(self.image_preview)
        preview_layout.addStretch()
        
        content_split.addWidget(self.preview_panel)

        # Right side: Metadata (Scrollable)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("ScrollArea")
        
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(20)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.content_container)
        content_split.addWidget(self.scroll_area)
        
        main_layout.addLayout(content_split)

        # Empty State
        self.empty_label = QLabel("No file selected. Please browse or drag and drop a file.")
        self.empty_label.setObjectName("EmptyStateLabel")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.empty_label)

        # Enable drag and drop
        self.setAcceptDrops(True)

    def apply_styles(self):
        # Modern Dark Theme CSS
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0F0F0F;
            }
            QWidget {
                color: #E0E0E0;
                font-family: 'Segoe UI Variable Display', 'Segoe UI', 'Roboto', 'Arial';
            }
            #ActionBar {
                background-color: #1A1A1A;
                border-radius: 12px;
                border: 1px solid #2A2A2A;
            }
            #PathEdit, #SearchEdit {
                background-color: #252525;
                border: 1px solid #3A3A3A;
                border-radius: 8px;
                padding: 10px 15px;
                font-size: 14px;
                color: #FFFFFF;
            }
            #PathEdit:focus, #SearchEdit:focus {
                border: 1px solid #0078D4;
                background-color: #2D2D2D;
            }
            #PrimaryButton {
                background-color: #0078D4;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 25px;
                font-weight: 600;
                font-size: 14px;
            }
            #PrimaryButton:hover {
                background-color: #1084D9;
            }
            #SecondaryButton {
                background-color: #333333;
                color: #FFFFFF;
                border: 1px solid #444444;
                border-radius: 8px;
                padding: 10px 25px;
                font-weight: 600;
                font-size: 14px;
            }
            #SecondaryButton:hover {
                background-color: #404040;
            }
            #ToolbarButton {
                background-color: #1E1E1E;
                color: #CCCCCC;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            #ToolbarButton:hover {
                background-color: #2A2A2A;
                color: #FFFFFF;
            }
            #ToolbarButton:disabled {
                color: #555555;
                border: 1px solid #222222;
            }
            #ScrollArea {
                border: none;
                background-color: transparent;
            }
            #MetadataCard {
                background-color: #1A1A1A;
                border: 1px solid #2A2A2A;
                border-radius: 12px;
            }
            #PreviewPanel {
                background-color: #1A1A1A;
                border: 1px solid #2A2A2A;
                border-radius: 12px;
                margin-right: 10px;
            }
            #CardTitle {
                font-size: 16px;
                font-weight: 700;
                color: #0078D4;
            }
            #Divider {
                background-color: #2A2A2A;
                height: 1px;
            }
            #KeyLabel {
                color: #999999;
                font-size: 13px;
            }
            #ValueLabel {
                color: #FFFFFF;
                font-size: 13px;
                font-weight: 500;
            }
            #CopyButton {
                background: transparent;
                border: none;
                color: #0078D4;
                font-size: 14px;
            }
            #CopyButton:hover {
                background: #252525;
                border-radius: 4px;
            }
            #EmptyStateLabel {
                font-size: 16px;
                color: #555555;
                margin-top: 150px;
            }
            #PreviewLabel {
                font-weight: bold;
                color: #0078D4;
                padding: 10px;
            }
            QScrollBar:vertical {
                border: none;
                background: #0F0F0F;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #333333;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #444444;
            }
        """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.file_path_edit.setText(file_path)
            self.start_extraction()

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            self.file_path_edit.setText(file_path)
            self.start_extraction()

    def start_extraction(self):
        path_str = self.file_path_edit.text().strip()
        if not path_str:
            return

        path = Path(path_str)
        if not path.exists():
            QMessageBox.warning(self, "Warning", f"File not found: {path_str}")
            return

        self.current_path = path
        self.extract_btn.setEnabled(False)
        self.extract_btn.setText("Processing...")
        
        self.worker = Worker(path_str)
        self.worker.finished.connect(self.on_extraction_finished)
        self.worker.error.connect(self.on_extraction_error)
        self.worker.start()

    @pyqtSlot(dict)
    def on_extraction_finished(self, data):
        self.current_data = data
        self.extract_btn.setEnabled(True)
        self.extract_btn.setText("View Metadata")
        self.export_json_btn.setEnabled(True)
        self.export_csv_btn.setEnabled(True)
        self.copy_all_btn.setEnabled(True)
        
        self.empty_label.hide()
        
        # Clear content layout
        for i in reversed(range(self.content_layout.count())): 
            widget = self.content_layout.itemAt(i).widget()
            if widget and widget != self.empty_label:
                widget.setParent(None)

        # Add cards
        for category, metadata in data.items():
            card = MetadataCard(category, metadata)
            self.content_layout.addWidget(card)

        # Handle Image Preview
        self.update_preview()

    def update_preview(self):
        if self.current_path and self.current_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']:
            pixmap = QPixmap(str(self.current_path))
            if not pixmap.isNull():
                self.image_preview.setPixmap(pixmap.scaled(
                    250, 250, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                ))
                self.preview_panel.show()
            else:
                self.preview_panel.hide()
        else:
            self.preview_panel.hide()

    @pyqtSlot(str)
    def on_extraction_error(self, error_msg):
        self.extract_btn.setEnabled(True)
        self.extract_btn.setText("View Metadata")
        QMessageBox.critical(self, "Error", f"Failed to extract metadata:\n{error_msg}")
        self.empty_label.show()
        self.preview_panel.hide()

    def filter_metadata(self, text):
        if not self.current_data:
            return
        
        text = text.lower()
        for i in range(self.content_layout.count()):
            card = self.content_layout.itemAt(i).widget()
            if isinstance(card, MetadataCard):
                has_match = False
                # Check title
                if text in card.findChild(QLabel, "CardTitle").text().lower():
                    has_match = True
                else:
                    # Check each row in the card
                    key_labels = card.findChildren(QLabel, "KeyLabel")
                    val_labels = card.findChildren(QLabel, "ValueLabel")
                    for k, v in zip(key_labels, val_labels):
                        if text in k.text().lower() or text in v.text().lower():
                            has_match = True
                            break
                card.setVisible(has_match)

    def export_json(self):
        if not self.current_data: return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save JSON", "metadata.json", "JSON Files (*.json)")
        if file_path:
            export_to_json(self.current_data, Path(file_path))
            QMessageBox.information(self, "Success", "Metadata exported to JSON successfully!")

    def export_csv(self):
        if not self.current_data: return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "metadata.csv", "CSV Files (*.csv)")
        if file_path:
            export_to_csv(self.current_data, Path(file_path))
            QMessageBox.information(self, "Success", "Metadata exported to CSV successfully!")

    def copy_all(self):
        if not self.current_data: return
        text = ""
        for cat, fields in self.current_data.items():
            text += f"[{cat}]\n"
            for k, v in fields.items():
                text += f"{k}: {v}\n"
            text += "\n"
        
        QGuiApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copied", "All metadata copied to clipboard!")

