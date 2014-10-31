#!/usr/bin/env python

import logging
import unittest
import getopt
import sys
import os

TEST_DIR = os.path.join(os.path.dirname(__file__), 'test')

def main():
    opts, args = getopt.getopt(sys.argv[1:], 'v')
    verbosity = 1

    for key, val in opts:
        if key == '-v':
            verbosity += 1

    logging.disable(logging.WARNING)

    suite = unittest.defaultTestLoader.discover(TEST_DIR)
    runner = unittest.TextTestRunner(verbosity=verbosity)
    runner.run(suite)

if __name__ == "__main__":
    main()
