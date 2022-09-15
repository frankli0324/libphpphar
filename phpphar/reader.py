from io import BytesIO
import warnings

from phpserialize import unserialize

import phpphar.types as types
from phpphar.constants import _HALT, _STUB_SFX
from phpphar.utils import _readuntil


def read_entry_manifest(stream: BytesIO, obj: 'types.Phar'):
    entry = types.PharEntry()
    name_len = int.from_bytes(stream.read(4), 'little')
    entry.name = stream.read(name_len)
    entry.size = int.from_bytes(stream.read(4), 'little')
    entry.timestamp = int.from_bytes(stream.read(4), 'little')
    entry.compressed_size = int.from_bytes(stream.read(4), 'little')
    entry.crc32 = stream.read(4)
    flags = int.from_bytes(stream.read(4), 'little')
    entry.permissions = types.PharEntryPermission(flags & 0x1ff)
    entry.flags = types.PharEntryFlag(flags & 0xfffffe00)
    metadata_len = int.from_bytes(stream.read(4), 'little')
    if metadata_len != 0:
        metadata_raw = stream.read(metadata_len)
        entry.metadata = unserialize(metadata_raw)
    obj.entries.append(entry)


def read_manifest(stream: BytesIO, obj: 'types.Phar'):
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
    obj.flags = types.PharGlobalFlag(int.from_bytes(stream.read(4), 'little'))
    alias_len = int.from_bytes(stream.read(4), 'little')
    obj.alias = stream.read(alias_len)
    metadata_len = int.from_bytes(stream.read(4), 'little')
    if metadata_len != 0:
        metadata_raw = stream.read(metadata_len)
        obj.metadata = unserialize(metadata_raw)
    manifest_len -= (4 + 4 + 2 + 4 + 4 + alias_len + 4 + metadata_len)
    for _ in range(entry_cnt):
        read_entry_manifest(stream, obj)


def write_phar(stream: BytesIO, obj: 'types.Phar'):
    for s in _STUB_SFX + ['']:
        if obj.stub.endswith(_HALT + s):
            break
    else:
        url = 'https://www.php.net/manual/en/phar.fileformat.stub.php'
        warnings.warn(f'stub not ended properly. see note in {url}')
    stream.write(obj.stub)
