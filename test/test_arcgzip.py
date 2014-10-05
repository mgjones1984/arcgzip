import unittest
from arcgzip import GzipFile, GzipInfo
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

class TestReadGzip(unittest.TestCase):
    ## TEST SETTINGS
    TEST_FILE = os.path.join(DATA_DIR, "test.txt.gz")
    FILE_ATTR = {
        "CM": 8,             # DEFLATE
        "FLG": 0b00001000,   # FNAME flag
        "MTIME": 1412132400, # '2014/10/1 12:00:00'
        "XFL": 0,
        "OS": 3,             # UNIX
        "FNAME": "test.txt"
    }
    FILE_CONTENTS = b"asparagus\n"

    ## Test cases
    def test_load_file(self):
        with GzipFile.open(self.TEST_FILE) as gzip:
            self.assertEqual(len(gzip.gzipinfos), 1)

    def test_check_attributes(self):
        with GzipFile.open(self.TEST_FILE) as gzip:
            info = gzip.gzipinfos[0]

            for key in self.FILE_ATTR:
                self.assertEqual(getattr(info, key), self.FILE_ATTR[key])

    def test_read_contents(self):
        with GzipFile.open(self.TEST_FILE) as gzip:
            fp = gzip.extract(self.FILE_ATTR["FNAME"])
            self.assertEqual(fp.read(), self.FILE_CONTENTS)

if __name__ == "__main__":
    unittest.main()
