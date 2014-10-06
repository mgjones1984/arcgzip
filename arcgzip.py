#!/usr/bin/env python

"""Read and write gzip archives."""

from __future__ import print_function
import struct
import zlib
import io
import time
import os
import sys

#--------------------
# Constants
#--------------------
HEADER_FORMAT = '<2sBBIBB'
HEADER_SIZE = 10

FOOTER_FORMAT = '<2I'
FOOTER_SIZE = 8

GZIPID = b'\x1f\x8b'

FTEXT = 1
FHCRC = 2
FEXTRA = 4
FNAME = 8
FCOMMENT = 16
FRESERVED = 224

BUFSIZE = 4096

FIELD_ENCODING = 'latin-1' # [RFC-1952] FNAME and FCOMMENT must consist of ISO-885901 chars.

#--------------------
# Exception
#--------------------
class GzipError(Exception):
    """ Base Exception """

#--------------------
# GzipInfo class
#--------------------
class GzipInfo:
    def __init__(self, CM=8, FLG=0, MTIME=0, XFL=0, OS=255, EXFIELD=b'', FNAME='', FCOMMENT='', CRC16=0):
        self.CM = CM
        self.FLG = FLG
        self.MTIME = MTIME
        self.XFL = XFL
        self.OS = OS
        self.EXFIELD = EXFIELD
        self.FNAME = FNAME
        self.FCOMMENT = FCOMMENT
        self.CRC16 = CRC16

    def __repr__(self):
        return '<GzipInfo FLG={}, MTIME={}, XFL={}, OS={}, EXFIELD={}, FNAME={}, FCOMMENT={}, CRC16={}'.format(
                    self.FLG, self.MTIME, self.XFL, self.OS, self.EXFIELD, self.FNAME, self.FCOMMENT, self.CRC16)

    @classmethod
    def fromgzipfile(cls, gzipfile):
        """Read a member from gzipfile. Return GzipInfo object"""
        obj = cls()

        ## Read the header
        buf = gzipfile.read(HEADER_SIZE)

        if not buf:
            return None
        elif len(buf) < HEADER_SIZE:
            raise GzipError('file header truncated')

        unpack = struct.unpack(HEADER_FORMAT, buf)

        if unpack[0] != GZIPID:
            raise GzipError('invalid file signature for gzip: {}'.format(unpack[0]))

        obj.CM, obj.FLG, obj.MTIME, obj.XFL, obj.OS = unpack[1:]

        if obj.CM != 8:
            raise GzipError('unknown compression method: {}'.format(obj.CM))
        elif obj.FLG & FRESERVED:
            # [RFC-1952] Reserved bits must be zero.
            raise GzipError('reserved bits are non-zero: {}'.format(obj.FLG))

        ## Read the extra header
        if obj.FLG & FEXTRA:
            XLEN = struct.unpack('<H', obj.fp.read(2))
            obj.EXFIELD = gzipfile.read(XLEN)

        if obj.FLG & FNAME:
            obj.FNAME = obj._read_str(gzipfile).decode(FIELD_ENCODING)
       
        if obj.FLG & FCOMMENT:
            obj.FCOMMENT = obj._read_str(gzipfile).decode(FIELD_ENCODING)

        if obj.FLG & FHCRC:
            obj.CRC16 = struct.unpack('<H', obj.fp.read(2))

        ## Skip the body part
        obj._data_offset = gzipfile.tell()
        decoder = zlib.decompressobj(-zlib.MAX_WBITS)

        while True:
            decoder.decompress(gzipfile.read(BUFSIZE))
            if decoder.unused_data != b'':
                gzipfile.seek(-len(decoder.unused_data), 1)
                break

        ## Read the footer
        obj.CRC32, obj.ISIZE = struct.unpack(FOOTER_FORMAT, gzipfile.read(FOOTER_SIZE))

        return obj

    @classmethod
    def fromfileobj(cls, fileobj):
        """Construct GzipInfo from a file object"""
        obj = cls()

        if hasattr(fileobj, 'name'):
            obj.FLG= obj.XFL | FNAME
            obj.FNAME = os.path.basename(fileobj.name)
            obj.MTIME = int(os.path.getmtime(fileobj.name))
        else:
            obj.MTIME = int(time.time())
    
        return obj

    def tobuf(self):
        """Convert self to gzip header bytes"""
        res = b''
        res += struct.pack(HEADER_FORMAT, GZIPID, self.CM, self.FLG, self.MTIME, self.XFL, self.OS)
 
        if self.FLG & FEXTRA:
            res += struct.pack('<H', self.XLEN)
            res += self.EXFIELD

        if self.FLG & FNAME:
            res += self.FNAME.encode(FIELD_ENCODING) + b'\x00'
       
        if self.FLG & FCOMMENT:
            res += self.FCOMMENT.encode(FIELD_ENCODING) + b'\x00'

        if self.FLG & FHCRC:
            res += self.pack('<H', self.CRC16)

        return res

    def _read_str(self, fp):
        """Read a zero terminated string"""
        res = b''

        while True:
            c = fp.read(1)
            if c == b'\x00':
                break
            res += c

        return res

#--------------------
# GzipFile class
#--------------------
class GzipFile:
    def __init__(self, fileobj=None, mode='r'):
        self.fileobj = fileobj
        self.mode = mode
        self.closed = False
        self.gzipinfos = []

        if mode == 'r':
            self._load()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    @classmethod
    def open(cls, filename, mode='r'):
        """Open a gzip archive. Return GzipInfo object"""

        if mode not in ('r', 'w', 'a'):
            raise ValueError("mode must be 'r', 'w' or 'a'")

        fileobj = open(filename, mode+'b')
        obj = cls(fileobj, mode=mode)

        return obj

    def _load(self):
        """Read through an entire archive to get the list of members"""
        self.gzipinfos = []

        while True:
            info = GzipInfo.fromgzipfile(self.fileobj)
            if not info:
                break
            self.gzipinfos.append(info)

    def close(self):
        """Close the file descripter"""
        self.closed = True
        self.fileobj.close()

    ### Methods to get meta data of the gzip file
    def getinfo(self, filename):
        """Search a member by filename. Return GzipInfo object (if found)"""

        if self.mode != 'r':
            raise IOError('file not open for reading')

        gzipinfos = self.getinfolist()

        for info in reversed(gzipinfos):
            if filename == info.FNAME:
                return info 

    def getinfolist(self):
        """Return the list of members in the archive."""

        if self.mode != 'r':
            raise IOError('file not open for reading')

        return self.gzipinfos

    ### Methods to extract/Add file objects
    def add(self, fileobj, gzipinfo=None, compresslevel=6):
        """Append a file to the end of the archive."""

        if self.mode not in ('w', 'a'):
            raise IOError('file not writible')

        if gzipinfo == None:
            gzipinfo = GzipInfo.fromfileobj(fileobj)

        self.fileobj.write(gzipinfo.tobuf())

        crc32, isize = 0, 0
        encoder = zlib.compressobj(compresslevel, zlib.DEFLATED, -zlib.MAX_WBITS)

        while True:
            data = fileobj.read(BUFSIZE)
            if data == b'':
                break
            crc32 = zlib.crc32(data, crc32)
            isize = (isize + len(data)) % 4294967296 # mod 2**32
            self.fileobj.write(encoder.compress(data))
        
        crc32 = crc32 & 0xffffffff
        self.fileobj.write(encoder.flush())

        self.fileobj.write(struct.pack(FOOTER_FORMAT, crc32, isize))

    def extract(self, filename=None, gzipinfo=None):
        """Extract a file from the archive. Return a file object."""

        if self.mode != 'r':
            raise IOError('file not open for reading')

        if filename:
            gzipinfo = self.getinfo(filename)

        if gzipinfo == None or gzipinfo not in self.gzipinfos:
            raise ValueError('Nothing to extract')

        self.fileobj.seek(gzipinfo._data_offset)

        buff = b''
        # We must set windowbits < 0 to get the data 
        # (de-)compressed in raw deflate format.
        # [zlib 1.2.8 Manual: VIII. Advanced Functions]
        decoder = zlib.decompressobj(-zlib.MAX_WBITS)

        while True:
            buff += decoder.decompress(self.fileobj.read(BUFSIZE))
            if decoder.unused_data != b'':
                break

        buff += decoder.flush()

        return io.BytesIO(buff)

    def addfile(self, filename, compresslevel=6):
        """Append the file (denoted by 'filename') to archive."""

        if self.mode not in ('w', 'a'):
            raise IOError('file not writible')

        with open(filename, 'rb') as fileobj:
            self.add(fileobj, compresslevel=compresslevel)

    def extractfile(self, filename):
        """Extract the 'filename' to the current working directory."""

        if self.mode != 'r':
            raise IOError('file not open for reading')

        info = self.getinfo(filename)

        if not info:
            raise ValueError("No such file in the archive: '{}'".format(filename))

        with open(filename, 'wb') as fw:
            fw.write(self.extract(gzipinfo=info).read())

        os.utime(filename, (int(time.time()), info.MTIME))

#--------------------
# Entry Point
#--------------------
def usage():
    print('usage: arcgzip.py [-l/--list] [-d/--decompress] [-h/--help] <gzipfile> [<filenames>]', file=sys.stderr)

def main():
    import getopt
    
    try: 
        from __builtin__ import raw_input as _input # python2.x compatibility
    except ImportError:
        _input = input

    COMPRESS, DECOMPRESS, LIST = 1, 2, 3
    action = COMPRESS
    compresslevel = 6

    # Parameter processing
    opts, args = getopt.getopt(sys.argv[1:], 'dlh', ('decompress', 'list', 'help'))
    for k,v in opts:
        if k == '-d' or k == '--decompress':
            action = DECOMPRESS
        elif k == '-l' or k == '--list':
            action = LIST
        elif k == '-h' or k == '--help':
            usage()
            sys.exit(0)

    if not args or (action == COMPRESS and len(args) < 2):
        usage()
        sys.exit(1)

    # Main
    if action == COMPRESS:
        with GzipFile.open(args[0], 'a') as gzip:
            for filename in args[1:]:
                print('adding: {}'.format(filename), file=sys.stderr)
                gzip.addfile(filename, compresslevel=compresslevel)

    elif action == DECOMPRESS:
        with GzipFile.open(args[0]) as gzip:
            if len(args) > 1:
                targets = args[1:]
            else:
                targets = set(info.FNAME for info in gzip.getinfolist() if info.FNAME)

            for filename in targets:
                if os.path.exists(filename):
                    if _input('{} exists. overwrite? [y/n]: '.format(filename)) != 'y':
                        continue
                print('extracting: {}'.format(filename), file=sys.stderr)
                gzip.extractfile(filename)

    elif action == LIST:
        with GzipFile.open(args[0]) as gzip:
            for info in gzip.getinfolist():
                print("'{}' <{}>".format(info.FNAME, time.ctime(info.MTIME)))

if __name__ == '__main__':
    main()
