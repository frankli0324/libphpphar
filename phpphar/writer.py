import bz2
from io import BytesIO
import warnings
import zlib

from phpserialize import serialize

import phpphar.types as types
from phpphar.constants import _HALT, _STUB_SFX, _PHAR_VERSION


def write_phar(stream: BytesIO, obj: 'types.Phar'):
    for s in _STUB_SFX + [b'']:
        if obj.stub.endswith(_HALT + s):
            break
    else:
        url = 'https://www.php.net/manual/en/phar.fileformat.stub.php'
        warnings.warn(f'stub not ended properly. see note in {url}')
    stream.write(obj.stub)
    write_manifest(stream, obj)


def write_manifest(stream, obj):
    manifest_len_cursor = stream.tell()
    stream.write(b'\0\0\0\0')  # placeholder for manifest length
    stream.write(len(obj.entries).to_bytes(4, 'little'))
    stream.write(_PHAR_VERSION)
    stream.write(obj.flags.value.to_bytes(4, 'little'))
    alias_bytes = obj.alias.encode('utf-8')
    stream.write(len(alias_bytes).to_bytes(4, 'little'))
    stream.write(alias_bytes)
    if obj.metadata != None:
        metadata_bytes = serialize(obj.metadata).encode('utf-8')
        stream.write(len(metadata_bytes).to_bytes(4, 'little'))
        stream.write(metadata_bytes)
    else:
        stream.write((0).to_bytes(4, 'little'))
    for entry in obj.entries:
        write_entry_manifest(stream, entry)
    manifest_len = stream.tell() - manifest_len_cursor - 4
    s, t = manifest_len_cursor, manifest_len_cursor + 4
    stream.getbuffer()[s:t] = manifest_len.to_bytes(4, 'little')


def write_entry_manifest(stream, entry):
    entry_name_bytes = entry.name.encode('utf-8')
    stream.write(len(entry_name_bytes).to_bytes(4, 'little'))
    stream.write(entry_name_bytes)
    stream.write(entry.size.to_bytes(4, 'little'))
    stream.write(entry.timestamp.to_bytes(4, 'little'))
    r_content = entry.content
    if types.PharEntryFlag.IS_BZIP2 in entry.flags:
        r_content = bz2.compress(entry.content)
    elif types.PharEntryFlag.IS_DEFLATE in entry.flags:
        r_content = zlib.compress(entry.content)
    stream.write(len(r_content).to_bytes(4, 'little'))
    stream.write(zlib.crc32(entry.content).to_bytes(4, 'little'))
    flags = entry.permissions | entry.flags.value
    stream.write(flags.to_bytes(4, 'little'))
    if entry.metadata != None:
        metadata_bytes = serialize(entry.metadata).encode('utf-8')
        stream.write(len(metadata_bytes).to_bytes(4, 'little'))
        stream.write(metadata_bytes)
    else:
        stream.write((0).to_bytes(4, 'little'))
