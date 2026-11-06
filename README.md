# 🔍 Python Metadata Viewer

A polished, modern, and professional Windows desktop application for viewing comprehensive file metadata.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-lightgrey.svg)

## ✨ Features

- **Modern Windows 11 Aesthetic**: Dark theme with Fluent Design principles, rounded corners, and elegant typography.
- **Comprehensive Metadata**:
  - **General**: File name, path, size, MIME type, extension.
  - **Timestamps**: Created, Modified, and Accessed times.
  - **Permissions**: Windows attributes and file mode.
  - **Checksums**: Instant MD5, SHA-1, and SHA-256 calculation.
  - **Image Specific**: Dimensions, Format, Color Mode, DPI, and full EXIF data extraction.
  - **Text Specific**: Line count and character count for text-based files.
- **Interactive UI**:
  - **Drag and Drop**: Quickly drop any file to view its metadata.
  - **Search & Filter**: Real-time filtering of metadata fields.
  - **Image Preview**: Visual preview for supported image formats.
  - **Export**: Save metadata to professional JSON or CSV reports.
  - **Clipboard**: Copy individual values or the entire metadata report with one click.
- **High Performance**: Asynchronous processing ensures the UI remains responsive even during heavy operations.
- **Privacy Focused**: Works entirely offline. No data ever leaves your computer.

## 🚀 Installation

### From Source

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/metadata-viewer.git
   cd metadata-viewer
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

### Windows Binary (Standalone)

To build a standalone executable:
1. Install PyInstaller: `pip install pyinstaller`
2. Run the build script: `python build_windows.py`
3. The executable will be in the `dist/MetadataViewer` folder.

## 🛠️ Built With

- **Python 3**
- **PyQt6**: For the modern, responsive user interface.
- **Pillow**: For advanced image metadata extraction.
- **Pathlib**: For robust cross-platform path handling.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
