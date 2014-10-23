import unittest
import os
from arcgzip import GzipFile, GzipInfo, GzipError, BadChecksum

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

class TestReadInvalidFiles(unittest.TestCase):
    EMPTY_FILE = os.path.join(DATA_DIR, "emptyfile.gz")
    EXBYTES_FILE =  os.path.join(DATA_DIR, "extrabytes.gz")
    EXMAGIC_FILE =  os.path.join(DATA_DIR, "extramagic.gz")
    ISIZE_FILE =  os.path.join(DATA_DIR, "badisize.gz")
    CRC32_FILE =  os.path.join(DATA_DIR, "badcrc32.gz")

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

    def test_bad_isize(self):
        with self.assertRaises(BadChecksum):
            with GzipFile.open(self.ISIZE_FILE) as gzip:
                pass

    def test_bad_crc32(self):
        with self.assertRaises(BadChecksum):
            with GzipFile.open(self.CRC32_FILE) as gzip:
                pass


if __name__ == "__main__":
    unittest.main()
