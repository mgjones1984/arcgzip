#!/usr/bin/env python

import logging
import unittest
import getopt
import sys

def main():
    opts, args = getopt.getopt(sys.argv[1:], 'v')
    verbosity = 1
    testdir = 'test/'

    for key, val in opts:
        if key == '-v':
            verbosity += 1

    logging.disable(logging.WARNING)

    suite = unittest.defaultTestLoader.discover(testdir)
    runner = unittest.TextTestRunner(verbosity=verbosity)
    runner.run(suite)

if __name__ == "__main__":
    main()
