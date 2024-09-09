import sys
from os.path import basename, dirname


class MissingType:
    def __repr__(self) -> str:
        return "MISSING"


MISSING = MissingType()

PROG = basename(sys.argv[0])

SUGAR_DIRNAME = dirname(__file__)
