from io import BytesIO

from phpserialize import unserialize

from .constants import _STUB_SFX
from .utils import _readuntil
from .types import Phar, PharGlobalFlag


def read_entry_manifest(stream: BytesIO, obj: Phar):
    pass


def read_manifest(stream: BytesIO, obj: Phar):
    obj.stub = _readuntil(stream, b'__HALT_COMPILER();')
    cursor = stream.tell()
    lookahead = stream.read(5)
    for s in _STUB_SFX:
        # `sorted` guarantees that longer patterns are matched first
        if lookahead.startswith(s):
            cursor += len(s)
            break
    stream.seek(cursor)
    manifest_len = int.from_bytes(stream.read(4), 'little')
    entry_cnt = int.from_bytes(stream.read(4), 'little')
    assert stream.read(2) == b'\x11\x00'
    obj.flags = PharGlobalFlag(int.from_bytes(stream.read(4), 'little'))
    alias_len = int.from_bytes(stream.read(4), 'little')
    obj.alias = stream.read(alias_len)
    metadata_len = int.from_bytes(stream.read(4), 'little')
    metadata_raw = stream.read(metadata_len)
    obj.metadata = unserialize(metadata_raw)
    manifest_len -= (4 + 4 + 2 + 4 + 4 + alias_len + 4 + metadata_len)


class PharBuilder:
    def __init__(self, archive: Phar):
        self.archive = archive

    def add_entry(self, name, content):
        pass

    def __bytes__(self):
        return bytes(self.archive)

    @staticmethod
    def load(data: bytes) -> Phar:
        obj = Phar()
        stream = BytesIO(data)
        read_manifest(stream, obj)
        return PharBuilder(obj)
