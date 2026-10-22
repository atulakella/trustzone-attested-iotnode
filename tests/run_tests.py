#!/usr/bin/env python3
"""Run the repository's host-side validation tests."""

import pathlib
import sys
import unittest


if __name__ == "__main__":
    root = pathlib.Path(__file__).resolve().parent
    suite = unittest.defaultTestLoader.discover(str(root), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not result.wasSuccessful())
