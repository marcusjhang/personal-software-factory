#!/usr/bin/env python3
"""Shim -> psf.adapters.codex. Kept for backward compatibility."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from psf.adapters.codex import main_cli  # noqa: E402

if __name__ == "__main__":
    main_cli(sys.argv[1:])
