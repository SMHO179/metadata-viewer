import json
import csv
from pathlib import Path
from typing import Dict, Any

def export_to_json(data: Dict[str, Dict[str, Any]], output_path: Path):
    """Exports metadata to a JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def export_to_csv(data: Dict[str, Dict[str, Any]], output_path: Path):
    """Exports metadata to a CSV file."""
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Category", "Field", "Value"])
        for category, fields in data.items():
            for field, value in fields.items():
                writer.writerow([category, field, value])
