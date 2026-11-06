import unittest
from pathlib import Path
from metadata_viewer.extractor import MetadataExtractor
import os

class TestMetadataExtractor(unittest.TestCase):
    def setUp(self):
        self.test_file = Path("test_sample.txt")
        with open(self.test_file, "w") as f:
            f.write("Hello, World!\nThis is a test file.")

    def tearDown(self):
        if self.test_file.exists():
            os.remove(self.test_file)

    def test_extract_all(self):
        data = MetadataExtractor.extract_all(self.test_file)
        self.assertIn("General", data)
        self.assertIn("Timestamps", data)
        self.assertEqual(data["General"]["File Name"], "test_sample.txt")
        self.assertEqual(data["General"]["Extension"], ".txt")
        self.assertIn("Checksums", data)
        self.assertIn("MD5", data["Checksums"])

    def test_text_metadata(self):
        data = MetadataExtractor.extract_all(self.test_file)
        self.assertIn("Text Info", data)
        self.assertEqual(data["Text Info"]["Line Count"], "2")

if __name__ == "__main__":
    unittest.main()
