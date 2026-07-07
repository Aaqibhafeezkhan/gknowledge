"""Entry point: ``python -m gknowledge`` and the ``gknowledge`` console script."""

import sys

from .app import main

if __name__ == "__main__":
    sys.exit(main(sys.argv))
