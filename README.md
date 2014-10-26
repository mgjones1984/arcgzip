arcgzip
=======

arcgzip.py is an alternative python gzip library, of which focus is
on the full support of gzip metadata.

Specifically, this library enables you to ...

* extract all of the meta information defined in [RFC-1952](http://www.gzip.org/zlib/rfc-gzip.html).
* create an archive with fine-tuned hearder data.
* handle multiple files in a single gzip archive.

Installation
------------

* Python 3.2 or later required (Python 2.7 is also supported)
* Download the source code and run 'setup.py':

    $ python setup.py install

Command-line Usage
------------------

    arcgzip.py -l archive.gz         - Show the list of contents.
    arcgzip.py -a archive.gz targets - Add target files to the archive.
    arcgzip.py -c archive.gz targets - Create a new archive from target files.
    arcgzip.py -d archive.gz targets - Extract files from the archive,

### Create/Append Options

    --ascii        - Set ASCII text flag.
    --crc16        - Add crc16 checksum field to the header.
    --comment [S]  - Add file comments for the file.
    --content [S]  - Write string to the archive (instead of adding target files)
    --encoding [S] - Specify the encoding of the string (with --content)
    --exfield <B>  - Set the base64-encoded data to the extra field.
    --level [N]    - Compression level to be used (1-fastest/9-slowest)

TODO
----

* Support stream input.
