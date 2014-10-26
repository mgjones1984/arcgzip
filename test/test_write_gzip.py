import unittest
import os
import tempfile
import shutil
from arcgzip import GzipFile, GzipInfo, GzipError, FTEXT

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

class TestWriteGzip(unittest.TestCase):
    FILE_NAME = 'textfile'
    TEST_FILE = os.path.join(DATA_DIR, FILE_NAME)

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_write_attributes(self):
        filepath = os.path.join(self.tmpdir, 'test.gz')

        with GzipFile.open(filepath, mode='w') as gzip:
            gzip.addfile(self.TEST_FILE)

        with GzipFile.open(filepath, mode='r') as gzip:
            info = gzip.getinfo(self.FILE_NAME)

            self.assertEqual(info.CM, 8)
            self.assertEqual(info.FLG, 0b00001000)
            self.assertEqual(info.MTIME, int(os.path.getmtime(self.TEST_FILE)))
            self.assertEqual(info.XFL, 0)
            self.assertEqual(info.FNAME, os.path.basename(self.TEST_FILE))

    def test_write_contents(self):
        filepath = os.path.join(self.tmpdir, 'test.gz')

        with GzipFile.open(filepath, mode='w') as gzip:
            gzip.addfile(self.TEST_FILE)

        with GzipFile.open(filepath, mode='r') as gzip, \
             open(self.TEST_FILE, mode='rb') as orig:

            fp = gzip.extract(self.FILE_NAME)
            self.assertEqual(fp.read(), orig.read())

    def test_best_compression(self):
        filepath = os.path.join(self.tmpdir, 'test.gz')

        with GzipFile.open(filepath, mode='w') as gzip:
            gzip.addfile(self.TEST_FILE, compresslevel=9)

        with GzipFile.open(filepath, mode='r') as gzip:
            info = gzip.getinfo(self.FILE_NAME)
            self.assertEqual(info.XFL, 2)

    def test_best_speed(self):
        filepath = os.path.join(self.tmpdir, 'test.gz')

        with GzipFile.open(filepath, mode='w') as gzip:
            gzip.addfile(self.TEST_FILE, compresslevel=1)

        with GzipFile.open(filepath, mode='r') as gzip:
            info = gzip.getinfo(self.FILE_NAME)
            self.assertEqual(info.XFL, 4)

    def test_file_comment(self):
        filepath = os.path.join(self.tmpdir, 'test.gz')
        comment = 'onion, shallot and garlic'

        with GzipFile.open(filepath, mode='w') as gzip:
            gzip.addfile(self.TEST_FILE, comment=comment)

        with GzipFile.open(filepath, mode='r') as gzip:
            info = gzip.getinfo(self.FILE_NAME)
            self.assertEqual(comment, info.FCOMMENT)

    def test_crc16(self):
        filepath = os.path.join(self.tmpdir, 'test.gz')

        with GzipFile.open(filepath, mode='w') as gzip:
            gzip.addfile(self.TEST_FILE, crc16=True)

        with GzipFile.open(filepath, mode='r') as gzip:
            info = gzip.getinfo(self.FILE_NAME)
            self.assertIsNotNone(info.CRC16)

    def test_ascii(self):
        filepath = os.path.join(self.tmpdir, 'test.gz')

        with GzipFile.open(filepath, mode='w') as gzip:
            gzip.addfile(self.TEST_FILE, isascii=True)

        with GzipFile.open(filepath, mode='r') as gzip:
            info = gzip.getinfo(self.FILE_NAME)
            self.assertTrue(info.FLG & FTEXT > 0)

    def test_exfield(self):
        filepath = os.path.join(self.tmpdir, 'test.gz')
        exfield = b'cp\x02\x08\x00'

        with GzipFile.open(filepath, mode='w') as gzip:
            gzip.addfile(self.TEST_FILE, exfield=exfield)

        with GzipFile.open(filepath, mode='r') as gzip:
            info = gzip.getinfo(self.FILE_NAME)
            self.assertEqual(exfield, info.EXFIELD)

    def test_write_data(self):
        filepath = os.path.join(self.tmpdir, 'test.gz')
        data = b'carrot, beet, radish and turnip'
        mtime = 1412132400 # 2014-10-01 12:00:00
        filename = 'roots_vagetables.txt'

        with GzipFile.open(filepath, mode='w') as gzip:
            gzip.adddata(data, mtime=mtime, filename=filename)

        with GzipFile.open(filepath, mode='r') as gzip:
            info = gzip.getinfo(filename)

            self.assertEqual(mtime, info.MTIME)
            self.assertEqual(filename, info.FNAME)

            fp = gzip.extract(gzipinfo=info)
            self.assertEqual(data, fp.read())

if __name__ == '__main__':
    unittest.main()
