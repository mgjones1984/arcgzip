#!/usr/bin/env python

import logging
import unittest

if __name__ == "__main__":
    logging.disable(logging.WARNING)

    suite = unittest.defaultTestLoader.discover('./test')
    runner = unittest.TextTestRunner()
    runner.run(suite)
