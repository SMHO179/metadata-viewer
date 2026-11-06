import sys
from PyQt6.QtWidgets import QApplication
from metadata_viewer.gui import ModernMetadataViewer

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Python Metadata Viewer")
    
    # Enable High DPI scaling if available in PyQt6
    # PyQt6 handles most of this automatically, but we can set defaults
    
    window = ModernMetadataViewer()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
