import unittest
import os
import io
from arcgzip import GzipFile, GzipInfo

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

class TestWriteGzip(unittest.TestCase):
    ## TEST SETTINGS
    TEST_FILE = os.path.join(DATA_DIR, "test.txt")

    ## Test cases
    def test_write_attributes(self):
        rawio = io.BytesIO()

        gzip_writable = GzipFile(rawio, mode="w")
        gzip_writable.addfile(self.TEST_FILE)

        rawio.seek(0)

        gzip_readable = GzipFile(rawio, mode="r")
        gzip_readable._load()

        info =  gzip_readable.gzipinfos[0]
    
        self.assertEqual(info.CM, 8)
        self.assertEqual(info.FLG, 0b00001000)
        self.assertEqual(info.MTIME, int(os.path.getmtime(self.TEST_FILE)))
        self.assertEqual(info.XFL, 0)
        self.assertEqual(info.FNAME, os.path.basename(self.TEST_FILE))

    def test_write_contents(self):
        rawio = io.BytesIO()

        gzip_writable = GzipFile(rawio, mode="w")
        gzip_writable.addfile(self.TEST_FILE)

        rawio.seek(0)

        gzip_readable = GzipFile(rawio, mode="r")
        gzip_readable._load()

        extr = gzip_readable.extract(os.path.basename(self.TEST_FILE))
        orig = open(self.TEST_FILE, "rb")

        self.assertEqual(extr.read(), orig.read())
        
if __name__ == "__main__":
    unittest.main()
