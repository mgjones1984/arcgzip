import unittest
import os
import io
import tempfile
import shutil
from arcgzip import GzipFile, GzipInfo, GzipError

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

    def test_extract_file(self):
        tmpdir = None
        try:
            tmpdir = tempfile.mkdtemp()
            os.chdir(tmpdir)

            with GzipFile.open(self.TEST_FILE) as gzip:
                filename = self.FILE_ATTR["FNAME"]
                gzip.extractfile(filename)

                stat = os.stat(filename)
                self.assertEqual(stat.st_mtime, self.FILE_ATTR["MTIME"])
                self.assertEqual(stat.st_size, len(self.FILE_CONTENTS))
        finally:
            if tmpdir:
                shutil.rmtree(tmpdir)

class TestReadInvalidFiles(unittest.TestCase):
    EMPTY_FILE = os.path.join(DATA_DIR, "emptyfile.gz")
    EXBYTES_FILE =  os.path.join(DATA_DIR, "extrabytes.gz")
    EXMAGIC_FILE =  os.path.join(DATA_DIR, "extramagic.gz")

    def test_read_emptyfile(self):
        with self.assertRaises(IOError):
            with GzipFile.open(self.EMPTY_FILE) as gzip:
                pass

    def test_extra_bytes(self):
        """ Test case for files with trailing garbage bytes """
        with GzipFile.open(self.EXBYTES_FILE) as gzip:
            self.assertEqual(len(gzip.gzipinfos), 1)

    def test_extra_magic(self):
        """ Special case in which trailing bytes are magic numbers"""
        with self.assertRaises(GzipError):
            with GzipFile.open(self.EXMAGIC_FILE) as gzip:
                pass

class TestWriteGzip(unittest.TestCase):
    ## TEST SETTINGS
    TEST_FILE = os.path.join(DATA_DIR, "test.txt")

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    ## Test cases
    def test_write_attributes(self):
        filepath = os.path.join(self.tmpdir, "test.gz")

        with GzipFile.open(filepath, mode="w") as gzip:
            gzip.addfile(self.TEST_FILE)

        with GzipFile.open(filepath, mode="r") as gzip:
            info = gzip.getinfo("test.txt")

            self.assertEqual(info.CM, 8)
            self.assertEqual(info.FLG, 0b00001000)
            self.assertEqual(info.MTIME, int(os.path.getmtime(self.TEST_FILE)))
            self.assertEqual(info.XFL, 0)
            self.assertEqual(info.FNAME, os.path.basename(self.TEST_FILE))

    def test_write_contents(self):
        filepath = os.path.join(self.tmpdir, "test.gz")

        with GzipFile.open(filepath, mode="w") as gzip:
            gzip.addfile(self.TEST_FILE)

        with GzipFile.open(filepath, mode="r") as gzip, \
             open(self.TEST_FILE, mode="rb") as orig:

            fp = gzip.extract("test.txt")
            self.assertEqual(fp.read(), orig.read())

if __name__ == "__main__":
    unittest.main()