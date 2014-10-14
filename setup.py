from distutils.core import setup

setup(
    name="arcgzip",
    version="20141001",
    py_modules=["arcgzip"],
    author="Fujimoto Seiji",
    author_email="fujimoto@writingarchives.sakura.ne.jp",
    url="https://github.com/fujimotos/arcgzip",
    description="Metadata-aware gzip archiver",
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
