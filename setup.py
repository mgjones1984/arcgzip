from distutils.core import setup

setup(
    name="arcgzip",
    version="20141001",
    author="Seiji Fujimoto",
    author_email="fujimoto@writingarchives.sakura.ne.jp",
    url="https://github.com/fujimotos/arcgzip",
    description="Read and write gzip as an archive format",
    long_description="""\
arcgzip.py is an experimental library to read and write gzip-format files.
Its main advantages over the stdlib gzip module is the more comprehensive
extraction of metadata and the ability of handling multiple files in a
single gzip archive. """,
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Topic :: System :: Archiving :: Compression"
    ]
)
