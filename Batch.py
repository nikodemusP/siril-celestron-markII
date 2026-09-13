import sys

import sirilpy as s
from sirilpyBatch.sirilpyBatch import sirilBatch

s.ensure_installed("PyQt6", "numpy", "astropy")

if __name__ == "__main__":
    sirilBatch(sys.argv)
