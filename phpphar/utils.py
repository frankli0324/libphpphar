from io import BytesIO
from phpserialize import unserialize

from .constants import *
from .types import Phar


def _readuntil(stream: BytesIO, pattern: bytes):
    matched = 0
    buffer = bytes()
    while matched < len(pattern):
        if (char := stream.read(1))[0] == pattern[matched]:
            matched += 1
        else:
            matched = 0
        if not char:
            break
        buffer += char
    return buffer
