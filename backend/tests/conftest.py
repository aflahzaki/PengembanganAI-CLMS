"""Pytest configuration and shared fixtures."""

import sys
from pathlib import Path

# Ensure backend directory is in Python path for all tests
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
