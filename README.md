arcgzip
=======

arcgzip.py is an alternative python library for gzip, of which focus
is on the full support of gzip metadata.

Specifically, this library enables you to ...

* extract all of the meta information defined in [RFC 1952](http://www.gzip.org/zlib/rfc-gzip.html):

  1. Original file name
  2. File comments
  3. Last-modified time of the original file
  4. Operating system on which the compression occured
  5. All kinds of the checksum values (CRC16, CRC32 and ISIZE)
  6. Extra field value, flags and etc.

* create an archive with fine-tuned hearder data.

Installation
------------

* Python 3.2 or later required (Python 2.7 is also supported)
* Download the source code and run 'setup.py':

  $ python setup.py install


TODO
----

* Support stream input.
