arcgzip
=======

arcgzip.py is an alternative python library for gzip, of which focus
is on the full support of gzip metadata.

Specifically, this library enables you to ...

* extract all of the meta information defined in [RFC-1952](http://www.gzip.org/zlib/rfc-gzip.html).
* create an archive with fine-tuned hearder data.

Installation
------------

* Python 3.2 or later required (Python 2.7 is also supported)
* Download the source code and run 'setup.py':

    $ python setup.py install


Usage
-----

### List all of the metadata within an archive

Running the installed module from the command line as follows:

    python -m arcgzip --list datafile.gz

This will give you an output like this:

    ---
    method:   8
    flg:      8
    mtime:    1412132400
    xfl:      0
    os:       3
    exfield:  None
    filename: test.txt
    comments: None
    crc16:    None
    crc32:    1738832628
    isize:    10
    ---


TODO
----

* Support stream input.
