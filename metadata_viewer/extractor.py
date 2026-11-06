import os
import sys
import stat
import time
import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from PIL import Image, ExifTags
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


def format_size(size_bytes: int) -> str:
    """Formats file size into human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} Bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB ({size_bytes:,} Bytes)"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB ({size_bytes:,} Bytes)"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB ({size_bytes:,} Bytes)"


class MetadataExtractor:
    """Extracts general and format-specific metadata from files."""

    @staticmethod
    def extract_all(path: Path, include_hashes: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        Extracts all metadata for a given path, organized by category.
        """
        path = Path(path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        result: Dict[str, Dict[str, Any]] = {
            "General": {},
            "Timestamps": {},
            "Permissions": {},
        }

        # General metadata
        stat_info = path.stat()
        result["General"]["File Name"] = path.name
        result["General"]["Folder Path"] = str(path.parent)
        result["General"]["Full Path"] = str(path)
        result["General"]["Size"] = format_size(stat_info.st_size)
        result["General"]["Raw Size (Bytes)"] = str(stat_info.st_size)
        
        mime_type, encoding = mimetypes.guess_type(path)
        result["General"]["MIME Type"] = mime_type or "Unknown"
        if encoding:
            result["General"]["Encoding"] = encoding

        ext = path.suffix.lower()
        result["General"]["Extension"] = ext if ext else "None"

        if path.is_dir():
            result["General"]["Type"] = "Directory"
        elif path.is_file():
            result["General"]["Type"] = "Regular File"
        elif path.is_symlink():
            result["General"]["Type"] = "Symbolic Link"
        else:
            result["General"]["Type"] = "Special File"

        # Timestamps
        # Creation time: st_ctime on Windows, st_birthtime on macOS/BSD if available
        try:
            ctime_val = getattr(stat_info, "st_birthtime", stat_info.st_ctime)
            result["Timestamps"]["Created"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ctime_val))
        except Exception:
            result["Timestamps"]["Created"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat_info.st_ctime))

        result["Timestamps"]["Modified"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat_info.st_mtime))
        result["Timestamps"]["Accessed"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat_info.st_atime))

        # Windows/Posix specific permissions
        if os.name == "nt":
            # Windows File Attributes
            attrs = []
            try:
                import win32api, win32con
                # We can fallback to stat if win32api isn't installed
            except ImportError:
                pass
            
            # Simple Windows stat checks
            if not os.access(path, os.W_OK):
                attrs.append("Read-Only")
            else:
                attrs.append("Read/Write")
            
            result["Permissions"]["Attributes"] = ", ".join(attrs) if attrs else "Normal"
        else:
            mode = stat_info.st_mode
            result["Permissions"]["Mode"] = stat.filemode(mode)
            try:
                result["Permissions"]["Owner (UID)"] = str(stat_info.st_uid)
                result["Permissions"]["Group (GID)"] = str(stat_info.st_gid)
            except AttributeError:
                pass

        result["Permissions"]["Hard Links"] = str(stat_info.st_nlink)

        # Calculate checksums if requested and if it's a file
        if include_hashes and path.is_file() and stat_info.st_size <= 500 * 1024 * 1024:  # 500MB limit for sync
            hashes = MetadataExtractor.compute_hashes(path)
            if hashes:
                result["Checksums"] = hashes

        # Image Metadata
        if HAS_PILLOW and path.is_file() and mime_type and mime_type.startswith("image/"):
            image_meta = MetadataExtractor.extract_image_metadata(path)
            if image_meta:
                result["Image Details"] = image_meta["basic"]
                if "exif" in image_meta and image_meta["exif"]:
                    result["EXIF Data"] = image_meta["exif"]

        # Text Metadata
        if path.is_file() and (mime_type and (mime_type.startswith("text/") or mime_type in ["application/json", "application/xml", "application/javascript"])):
            text_meta = MetadataExtractor.extract_text_metadata(path, stat_info.st_size)
            if text_meta:
                result["Text Info"] = text_meta

        return result

    @staticmethod
    def compute_hashes(path: Path) -> Dict[str, str]:
        """Compute MD5, SHA-1, and SHA-256 for a file."""
        md5 = hashlib.md5()
        sha1 = hashlib.sha1()
        sha256 = hashlib.sha256()

        try:
            with open(path, "rb") as f:
                while chunk := f.read(65536):
                    md5.update(chunk)
                    sha1.update(chunk)
                    sha256.update(chunk)
            return {
                "MD5": md5.hexdigest(),
                "SHA-1": sha1.hexdigest(),
                "SHA-256": sha256.hexdigest(),
            }
        except Exception as e:
            return {"Error": f"Could not compute checksums: {str(e)}"}

    @staticmethod
    def extract_image_metadata(path: Path) -> Dict[str, Dict[str, str]]:
        """Extract image specific metadata and EXIF data."""
        res: Dict[str, Dict[str, str]] = {"basic": {}, "exif": {}}
        try:
            with Image.open(path) as img:
                w, h = img.size
                mp = (w * h) / 1_000_000
                res["basic"]["Dimensions"] = f"{w} x {h} pixels ({mp:.2f} MP)"
                res["basic"]["Format"] = str(img.format)
                res["basic"]["Color Mode"] = str(img.mode)
                
                dpi = img.info.get("dpi")
                if dpi:
                    res["basic"]["DPI"] = f"{dpi[0]} x {dpi[1]}"

                # EXIF Data
                exif_data = {}
                if hasattr(img, "_getexif") and img._getexif():
                    raw_exif = img._getexif()
                    if raw_exif:
                        for tag_id, value in raw_exif.items():
                            tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                            # Filter or clean binary values
                            if isinstance(value, bytes):
                                if len(value) > 30:
                                    value = f"<{len(value)} bytes binary data>"
                                else:
                                    try:
                                        value = value.decode("utf-8", errors="replace")
                                    except Exception:
                                        value = str(value)
                            elif isinstance(value, tuple) and len(value) > 10:
                                value = f"<tuple of length {len(value)}>"

                            exif_data[str(tag_name)] = str(value)
                
                if exif_data:
                    res["exif"] = exif_data

        except Exception as e:
            res["basic"]["Image Reading Error"] = str(e)

        return res

    @staticmethod
    def extract_text_metadata(path: Path, size_bytes: int) -> Dict[str, str]:
        """Extract line count and character count for text files if reasonable size."""
        if size_bytes > 10 * 1024 * 1024:  # Skip line count for files > 10MB
            return {"Note": "File too large for text line analysis"}

        try:
            line_count = 0
            char_count = 0
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line_count += 1
                    char_count += len(line)

            return {
                "Line Count": f"{line_count:,}",
                "Character Count": f"{char_count:,}"
            }
        except Exception as e:
            return {"Error": f"Could not analyze text: {str(e)}"}
