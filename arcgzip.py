#!/usr/bin/env python

"""Metadata-aware gzip archiver

Command-line Usage:

  arcgzip.py -l archive.gz         - Show the list of contents.
  arcgzip.py -a archive.gz targets - Add target files to the archive.
  arcgzip.py -c archive.gz targets - Create a new archive from target files.
  arcgzip.py -d archive.gz targets - Extract files from the archive,

Create/Append Options:

  --ascii        - Set ASCII text flag.
  --crc16        - Add crc16 checksum field to the header.
  --comment <S>  - Add file comments for the file.
  --content <S>  - Write the string to archive (instead of target files)
  --encoding <S> - Specify the encoding of the string (with --content)
  --exfield <B>  - Set the base64-encoded data to the extra field.
  --level <N>    - Compression level to be used (1-fastest/9-slowest)
"""

from __future__ import print_function
import struct
import logging
import zlib
import io
import time
import os
import sys

#--------------------
# gzip constants
#--------------------
HEADER_FORMAT = '<2sBBIBB'
HEADER_SIZE = 10

FOOTER_FORMAT = '<2I'
FOOTER_SIZE = 8

GZIP_MAGIC = b'\x1f\x8b'

FTEXT = 1
FHCRC = 2
FEXTRA = 4
FNAME = 8
FCOMMENT = 16
FRESERVED = 224

# [RFC-1952] FNAME and FCOMMENT must consist of ISO-885901 chars.
FIELD_ENCODING = 'latin-1'

#--------------------
# arcgzip constants
#--------------------
Z_BEST_SPEED = 1        # The compression level must be an integer
Z_BEST_COMPRESSION = 9  # between 1 (fastest) and 9 (slowest).

BUFSIZE = 1024 * 16

TEMPLATE_FULL = """\
---
method:   {CM}
flg:      {FLG}
mtime:    {MTIME}
xfl:      {XFL}
os:       {OS}
exfield:  {EXFIELD}
filename: {FNAME}
comments: {FCOMMENT}
crc16:    {CRC16}
crc32:    {CRC32}
isize:    {ISIZE}
---"""

#--------------------
# Exceptions
#--------------------
class GzipError(Exception):
    """ Base Exception """

class EmptyHeader(GzipError):
    """ Exception for empty header """

class BadMagicNumber(GzipError):
    """ Exception for invalid header magic bytes """

class BadChecksum(GzipError):
    """ Exception for bad checksum"""

#--------------------
# Utility functions
#--------------------
def _read_to_zero(fp):
    """Read a zero terminated byte sequence"""
    res = b''

    while True:
        c = fp.read(1)
        if not c:
            return None # Reach EOF before end of string
        elif c == b'\x00':
            break
        res += c

    return res

#--------------------
# GzipInfo class
#--------------------
class GzipInfo:
    def __init__(self, CM=8, FLG=0, MTIME=0, XFL=0, OS=255, EXFIELD=None, FNAME=None, FCOMMENT=None):
        self.CM = CM
        self.FLG = FLG
        self.MTIME = MTIME
        self.XFL = XFL
        self.OS = OS
        self.EXFIELD = EXFIELD
        self.FNAME = FNAME
        self.FCOMMENT = FCOMMENT

        self.CRC16 = None
        self.CRC32 = None
        self.ISIZE = None

        # The byte offset relative to the start of file.
        # This property is meant to be used only internally.
        self._data_offset = None

    def __repr__(self):
        return '<GzipInfo FLG={}, MTIME={}, XFL={}, OS={}, EXFIELD={}, FNAME={}, FCOMMENT={}>'.format(
                    self.FLG, self.MTIME, self.XFL, self.OS, self.EXFIELD, self.FNAME, self.FCOMMENT)

    @classmethod
    def fromgzipfile(cls, gzipfile):
        """Read a member from gzipfile. Return GzipInfo object"""
        obj = cls()

        # Read the header
        buf = gzipfile.read(HEADER_SIZE)

        if not buf:
            raise EmptyHeader('empty header')

        if buf[:2] != GZIP_MAGIC:
            raise BadMagicNumber('magic header is not present')

        if len(buf) < HEADER_SIZE:
            raise GzipError('file header truncated')

        unpack = struct.unpack(HEADER_FORMAT, buf)

        obj.CM, obj.FLG, obj.MTIME, obj.XFL, obj.OS = unpack[1:]

        if obj.CM != 8:
            raise GzipError('unknown compression method: {}'.format(obj.CM))
        elif obj.FLG & FRESERVED:
            # [RFC-1952] Reserved bits must be zero.
            raise GzipError('reserved bits are non-zero: {}'.format(obj.FLG))

        # Read the extra header
        exbuf = b''
        if obj.FLG & FEXTRA:
            XLEN = gzipfile.read(2)
            obj.EXFIELD = gzipfile.read(struct.unpack('<H', XLEN)[0])

            exbuf += (XLEN + obj.EXFIELD)

        if obj.FLG & FNAME:
            bs = _read_to_zero(gzipfile)
            if bs is None:
                raise GzipError('could not read the name of file')
            exbuf += bs + b'\0'
            obj.FNAME = bs.decode(FIELD_ENCODING)
       
        if obj.FLG & FCOMMENT:
            bs = _read_to_zero(gzipfile)
            if bs is None:
                raise GzipError('could not read the file comment')
            exbuf += bs + b'\0'
            obj.FCOMMENT = bs.decode(FIELD_ENCODING)

        if obj.FLG & FHCRC:
            obj.CRC16 = struct.unpack('<H', gzipfile.read(2))[0]

            crc16 = (zlib.crc32(buf+exbuf) & 0xffffffff) % 0x10000
            if crc16 != obj.CRC16:
                raise BadChecksum('invalid CRC16 checksum: {} != {}'.format(crc16, obj.CRC16))

        # Skip the body part
        obj._data_offset = gzipfile.tell()
        decoder = zlib.decompressobj(-zlib.MAX_WBITS)

        crc32, isize = 0, 0
        while True:
            data = decoder.decompress(gzipfile.read(BUFSIZE))

            crc32 = zlib.crc32(data, crc32)
            isize = (isize + len(data)) % 0x100000000

            if decoder.unused_data != b'':
                gzipfile.seek(-len(decoder.unused_data), 1)
                break

        data = decoder.flush()
        crc32 = zlib.crc32(data, crc32) & 0xffffffff
        isize = (isize + len(data)) % 0x100000000

        # Read the footer
        obj.CRC32, obj.ISIZE = struct.unpack(FOOTER_FORMAT, gzipfile.read(FOOTER_SIZE))

        if crc32 != obj.CRC32:
            raise BadChecksum('invalid CRC32 checksum: {} != {}'.format(crc32, obj.CRC32))
        elif isize != obj.ISIZE:
            raise BadChecksum('incorrect file length: {} != {}'.format(isize, obj.ISIZE))

        return obj

    @classmethod
    def fromfilepath(cls, filepath):
        info = cls()

        info.FLG = info.XFL | FNAME
        info.FNAME = os.path.basename(filepath)
        info.MTIME = int(os.path.getmtime(filepath))

        return info

    @classmethod
    def fromfileobj(cls, fileobj):
        """Construct GzipInfo from a file object"""

        if hasattr(fileobj, 'name') and os.path.exists(fileobj.name):
            info = cls.fromfilepath(fileobj.name)
        else:
            info = cls()
            info.MTIME = int(time.time())
    
        return info

    def set_filename(self, filename):
        """Set the file name and activate the corresponding
           flag bit.
        """
        self.FLG = self.FLG | FNAME
        self.FNAME = filename

    def set_extra_flag(self, compresslevel):
        """Set the extra flag assuming DEFLATE compression
           method is used.
        """
        flg = 0
        if compresslevel == Z_BEST_COMPRESSION:
            flg = 2
        elif compresslevel == Z_BEST_SPEED:
            flg = 4

        self.XFL = flg

    def set_operating_system(self):
        """Set the flag value which indicate the type
           of the operating system.
        """
        flg = 255 # unknown operating system
        if sys.platform.startswith('win32'):
            flg = 0
        elif sys.platform.startswith('linux'):
            flg = 3
        elif sys.platform.startswith('darwin'):
            flg = 7

        self.OS = flg

    def set_file_comment(self, comment):
        """Set the file comment and activate the corresponding
           flag bit.
        """
        self.FLG = self.FLG | FCOMMENT
        self.FCOMMENT = comment

    def set_crc16(self):
        """Set the flag bit for CRC16 header checksum"""

        # Actual CRC16 value must be calculated right before writing
        # to the output file (to avoid the corruption of the resulting 
        # archive).
        self.FLG = self.FLG | FHCRC

    def set_ascii(self):
        """Set the flag bit indicating that the content is
           ASCII text.
        """
        self.FLG = self.FLG | FTEXT

    def set_exfield(self, exfield):
        """Set the binary data to the extra field."""
        self.FLG = self.FLG | FEXTRA
        self.EXFIELD = exfield

    def tobuf(self):
        """Convert self to gzip header bytes"""
        res = b''
        res += struct.pack(HEADER_FORMAT, GZIP_MAGIC, self.CM, self.FLG, self.MTIME, self.XFL, self.OS)
 
        if self.FLG & FEXTRA:
            res += struct.pack('<H', len(self.EXFIELD))
            res += self.EXFIELD

        if self.FLG & FNAME:
            res += self.FNAME.encode(FIELD_ENCODING) + b'\x00'
       
        if self.FLG & FCOMMENT:
            res += self.FCOMMENT.encode(FIELD_ENCODING) + b'\x00'

        if self.FLG & FHCRC:
            crc16 = (zlib.crc32(res) & 0xffffffff) % 65536
            res += struct.pack('<H', crc16)

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

        try:
            if mode == 'r':
                self._load()
        except:
            fileobj.close()
            raise

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
            try:
                info = GzipInfo.fromgzipfile(self.fileobj)
            except EmptyHeader:
                if self.gzipinfos:
                    break
                raise IOError('file is empty')
            except BadMagicNumber as e:
                if self.gzipinfos:
                    logging.warning('trailing garbage bytes ignored')
                    break
                raise IOError('file is not gzip format')
            self.gzipinfos.append(info)

    def close(self):
        """Close the file descripter"""
        self.closed = True
        self.fileobj.close()

    def getinfo(self, filename):
        """Search a member by filename. Return GzipInfo object."""

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

    # Methods to add/extract file object. The other gzip-manipulating
    # methods are built on these functions.
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
            isize = (isize + len(data)) % 0x100000000
            self.fileobj.write(encoder.compress(data))
        
        crc32 = crc32 & 0xffffffff
        self.fileobj.write(encoder.flush())

        self.fileobj.write(struct.pack(FOOTER_FORMAT, crc32, isize))

    def extract(self, filename=None, gzipinfo=None):
        """Extract a file from the archive as a file object."""

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

    # Methods to manipulate the files on the current working
    # directory.
    def addfile(self, filepath, compresslevel=6, exfield=None, comment=None,
                crc16=False, isascii=False):
        """Write the contents of <filepath> to the archive with the specified
           attributes.
        """

        if self.mode not in ('w', 'a'):
            raise IOError('file not writible')

        info = GzipInfo.fromfilepath(filepath)
        info.set_operating_system()
        info.set_extra_flag(compresslevel)

        if exfield:
            info.set_exfield(exfield)

        if comment:
            info.set_file_comment(comment)

        if crc16:
            info.set_crc16()

        if isascii:
            info.set_ascii()

        with open(filepath, 'rb') as fileobj:
            self.add(fileobj, gzipinfo=info, compresslevel=compresslevel)

    def extractfile(self, filename):
        """Extract <filename> to the current working directory."""

        if self.mode != 'r':
            raise IOError('file not open for reading')

        info = self.getinfo(filename)

        if not info:
            raise ValueError("No such file in the archive: '{}'".format(filename))

        with open(filename, 'wb') as fw:
            fw.write(self.extract(gzipinfo=info).read())

        os.utime(filename, (int(time.time()), info.MTIME))

    def adddata(self, data, compresslevel=6, mtime=None, filename=None, exfield=None,
                comment=None, crc16=False, isascii=False):
        """Add binary data to the end of the archive"""

        if self.mode not in ('w', 'a'):
            raise IOError('file not writible')

        info = GzipInfo()
        info.set_operating_system()
        info.set_extra_flag(compresslevel)

        if mtime is not None:
            info.MTIME = mtime
        else:
            info.MTIME = int(time.time())

        if filename:
            info.set_filename(filename)

        if exfield:
            info.set_exfield(exfield)

        if comment:
            info.set_file_comment(comment)

        if crc16:
            info.set_crc16()

        if isascii:
            info.set_ascii()

        self.add(io.BytesIO(data), gzipinfo=info, compresslevel=compresslevel)

#--------------------
# Entry Point
#--------------------
def main():
    import getopt
    from base64 import b64decode
    
    logging.basicConfig(format='arcgzip: %(message)s', level=logging.INFO)

    try: 
        from __builtin__ import raw_input as _input # python2.x compatibility
    except ImportError:
        _input = input

    COMPRESS, DECOMPRESS, LIST = 1, 2, 3
    action, archive, mode = None, None, None
    compresslevel = 6
    comment = None
    exfield = None
    crc16 = False
    isascii = False
    content = None
    encoding = 'utf-8'

    # Parameter processing
    shortopts = 'a:c:d:l:'
    longopts = ('level=', 'comment=', 'content=', 'exfield=', 'encoding=', 'ascii', 'crc16', 'help')

    opts, args = getopt.getopt(sys.argv[1:], shortopts, longopts)
    for key,val in opts:
        if key == '-a':
            action = COMPRESS
            archive, mode = val, 'a'
        elif key == '-c':
            action = COMPRESS
            archive, mode = val, 'w'
        elif key == '-d':
            action = DECOMPRESS
            archive = val
        elif key == '-l':
            action = LIST
            archive = val
        elif key == '--level':
            compresslevel = int(val)
        elif key == '--comment':
            comment = val
        elif key == '--content':
            content = val
        elif key == '--exfield':
            exfield = b64decode(val)
        elif key == '--encoding':
            encoding = val
        elif key == '--crc16':
            crc16 = True
        elif key == '--ascii':
            isascii = True
        elif key == '--help':
            print(__doc__, file=sys.stderr)
            sys.exit(0)

    if not action or (action == COMPRESS and not (args or content)):
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    # Main
    if action == COMPRESS and content:
        with GzipFile.open(archive, mode=mode) as gzip:
            data = content.encode(encoding)
            gzip.adddata(data, compresslevel=compresslevel, exfield=exfield,
                         comment=comment, crc16=crc16, isascii=isascii)

    elif action == COMPRESS and args:
        with GzipFile.open(archive, mode=mode) as gzip:
            for filename in args:
                if not os.path.exists(filename) or not os.path.isfile(filename):
                    logging.warning("'{}' is not a regular file".format(filename))
                    continue
                elif os.path.samefile(archive, filename):
                    logging.warning("'{}' skipped".format(filename))
                    continue

                logging.info('adding: {}'.format(filename))
                gzip.addfile(filename, compresslevel=compresslevel, exfield=exfield,
                             comment=comment, crc16=crc16, isascii=isascii)

    elif action == DECOMPRESS:
        with GzipFile.open(archive) as gzip:
            if args:
                targets = args
            else:
                targets = set(info.FNAME for info in gzip.getinfolist() if info.FNAME)

            for filename in targets:
                if os.path.exists(filename):
                    if _input('{} exists. overwrite? [y/n]: '.format(filename)) != 'y':
                        continue
                logging.info('extracting: {}'.format(filename))
                gzip.extractfile(filename)

    elif action == LIST:
        with GzipFile.open(archive) as gzip:
            for info in gzip.getinfolist():
                print(TEMPLATE_FULL.format(**info.__dict__))

if __name__ == '__main__':
    main()
