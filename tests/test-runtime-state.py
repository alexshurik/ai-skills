#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path


def main() -> int:
    test_root = Path(__file__).with_name("runtime_state")
    suite = unittest.defaultTestLoader.discover(
        str(test_root),
        pattern="test_*.py",
        top_level_dir=str(test_root.parent),
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print("OK: runtime state")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
