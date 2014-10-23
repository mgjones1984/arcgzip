import unittest
import os
import tempfile
import shutil
from arcgzip import GzipFile, GzipInfo, GzipError

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

class TestReadGzip(unittest.TestCase):
    TEST_FILE = os.path.join(DATA_DIR, 'textfile.gz')
    FILE_ATTR = {
        'CM': 8,             # DEFLATE
        'FLG': 0b00001000,   # FNAME flag
        'MTIME': 1412132400, # '2014/10/1 12:00:00'
        'XFL': 0,
        'OS': 3,             # UNIX
        'FNAME': 'textfile'
    }
    FILE_CONTENTS = b'asparagus\n'

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
            fp = gzip.extract(self.FILE_ATTR['FNAME'])
            self.assertEqual(fp.read(), self.FILE_CONTENTS)

    def test_extract_file(self):
        tmpdir = None
        try:
            tmpdir = tempfile.mkdtemp()
            os.chdir(tmpdir)

            with GzipFile.open(self.TEST_FILE) as gzip:
                filename = self.FILE_ATTR['FNAME']
                gzip.extractfile(filename)

                stat = os.stat(filename)
                self.assertEqual(stat.st_mtime, self.FILE_ATTR['MTIME'])
                self.assertEqual(stat.st_size, len(self.FILE_CONTENTS))
        finally:
            if tmpdir:
                shutil.rmtree(tmpdir)

if __name__ == '__main__':
    unittest.main()
