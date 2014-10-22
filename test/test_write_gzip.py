import unittest
import os
import tempfile
import shutil
from arcgzip import GzipFile, GzipInfo, GzipError

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

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

    def test_best_compression(self):
        filepath = os.path.join(self.tmpdir, "test.gz")

        with GzipFile.open(filepath, mode="w") as gzip:
            gzip.addfile(self.TEST_FILE, compresslevel=9)

        with GzipFile.open(filepath, mode="r") as gzip:
            info = gzip.getinfo("test.txt")
            self.assertEqual(info.XFL, 2)

    def test_best_speed(self):
        filepath = os.path.join(self.tmpdir, "test.gz")

        with GzipFile.open(filepath, mode="w") as gzip:
            gzip.addfile(self.TEST_FILE, compresslevel=1)

        with GzipFile.open(filepath, mode="r") as gzip:
            info = gzip.getinfo("test.txt")
            self.assertEqual(info.XFL, 4)

    def test_file_comment(self):
        filepath = os.path.join(self.tmpdir, "test.gz")
        comment = 'onion, shallot and garlic'

        with GzipFile.open(filepath, mode="w") as gzip:
            gzip.addfile(self.TEST_FILE, comment=comment)

        with GzipFile.open(filepath, mode="r") as gzip:
            info = gzip.getinfo("test.txt")
            self.assertEqual(comment, info.FCOMMENT)

    def test_crc16(self):
        filepath = os.path.join(self.tmpdir, "test.gz")

        with GzipFile.open(filepath, mode="w") as gzip:
            gzip.addfile(self.TEST_FILE, crc16=True)

        with GzipFile.open(filepath, mode="r") as gzip:
            info = gzip.getinfo("test.txt")
            self.assertIsNotNone(info.CRC16)

if __name__ == "__main__":
    unittest.main()
