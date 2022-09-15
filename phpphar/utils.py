from bz2 import BZ2Decompressor
from io import BytesIO
import zlib


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


class DecompressReader:
    def __init__(self, stream: BytesIO, decompressor):
        self._stream = stream
        self._decompressor = decompressor
        self._buffer = BytesIO()

    def _update(self, size=-1):
        self._buffer.write(self._decompressor.decompress(
            self._stream.read(size)
        ))

    def read(self, size=-1, window=1024):
        if size == -1:
            self._update()
        else:
            cursor = self._buffer.tell()
            while self._buffer.getbuffer().nbytes - cursor < size:
                buf = self._decompressor.decompress(self._stream.read(window))
                self._buffer.write(buf)
            self._buffer.seek(cursor)
        return self._buffer.read(size)


class BZip2Reader(DecompressReader):
    def __init__(self, stream: BytesIO) -> None:
        super().__init__(stream, BZ2Decompressor())


class ZlibReader(DecompressReader):
    def __init__(self, stream: BytesIO) -> None:
        super().__init__(stream, zlib.decompressobj())
