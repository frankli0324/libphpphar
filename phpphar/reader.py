import hashlib
from io import BytesIO
import warnings
import zlib

from phpserialize import unserialize

import phpphar.types as types
from phpphar.constants import _HALT, _STUB_SFX
from phpphar.utils import BZip2Reader, ZlibReader, _readuntil


def read_entry_manifest(stream: BytesIO, obj: 'types.Phar'):
    entry = types.PharEntry()
    name_len = int.from_bytes(stream.read(4), 'little')
    entry.name = stream.read(name_len)
    entry.size = int.from_bytes(stream.read(4), 'little')
    entry.timestamp = int.from_bytes(stream.read(4), 'little')
    entry.compressed_size = int.from_bytes(stream.read(4), 'little')
    entry.crc32 = int.from_bytes(stream.read(4), 'little')
    flags = int.from_bytes(stream.read(4), 'little')
    entry.permissions = types.PharEntryPermission(flags & 0x1ff)
    entry.flags = types.PharEntryFlag(flags & 0xfffffe00)
    metadata_len = int.from_bytes(stream.read(4), 'little')
    if metadata_len != 0:
        metadata_raw = stream.read(metadata_len)
        entry.metadata = unserialize(metadata_raw)
    obj.entries.append(entry)


def read_manifest(stream: BytesIO, obj: 'types.Phar'):
    obj.stub = _readuntil(stream, _HALT)
    cursor = stream.tell()
    lookahead = stream.read(5)
    for s in _STUB_SFX:
        # `sorted` guarantees that longer patterns are matched first
        if lookahead.startswith(s):
            cursor += len(s)
            break
    stream.seek(cursor)
    manifest_len = int.from_bytes(stream.read(4), 'little')
    manifest_end = cursor + manifest_len + 4
    entry_cnt = int.from_bytes(stream.read(4), 'little')
    assert stream.read(2) == b'\x11\x00'
    obj.flags = types.PharGlobalFlag(int.from_bytes(stream.read(4), 'little'))
    alias_len = int.from_bytes(stream.read(4), 'little')
    obj.alias = stream.read(alias_len)
    metadata_len = int.from_bytes(stream.read(4), 'little')
    if metadata_len != 0:
        metadata_raw = stream.read(metadata_len)
        obj.metadata = unserialize(metadata_raw)
    for _ in range(entry_cnt):
        read_entry_manifest(stream, obj)
    if manifest_end != stream.tell():
        warnings.warn(
            'manifest length mismatch. '
            'possibly reading a broken phar'
        )


def read_contents(stream: BytesIO, obj: 'types.Phar'):
    for entry in obj.entries:
        # TODO: handle size mismatch
        # invalidate zip bombs
        if entry.flags == types.PharEntryFlag.IS_BZIP2:
            s = BytesIO(stream.read(entry.compressed_size))
            entry.content = BZip2Reader(s).read(entry.size)
        elif entry.flags == types.PharEntryFlag.IS_DEFLATE:
            s = BytesIO(stream.read(entry.compressed_size))
            entry.content = ZlibReader(s).read(entry.size)
        else:
            # TODO: handle multiple compression flags are set
            entry.content = stream.read(entry.size)
        if zlib.crc32(entry.content) != entry.crc32:
            warnings.warn(f'{entry.name} crc32 mismatch')


def verify_signature(stream: BytesIO, obj: 'types.Phar'):
    if types.PharGlobalFlag.SIGNED not in obj.flags:
        return
    content = stream.getbuffer()[:stream.tell()]
    signature = stream.read()
    if len(signature) <= 8 or not signature.endswith(b'GBMB'):
        warnings.warn('broken signature')
        return
    sign_flag = types.PharSignFlag(
        int.from_bytes(signature[-8:-4], 'little')
    )
    signature = signature[:-8]
    if types.PharSignFlag.MD5 in sign_flag:
        result = hashlib.md5(content).digest()
    elif types.PharSignFlag.SHA1 in sign_flag:
        result = hashlib.sha1(content).digest()
    elif types.PharSignFlag.SHA256 in sign_flag:
        result = hashlib.sha256(content).digest()
    elif types.PharSignFlag.OPENSSL in sign_flag:
        warnings.warn('TODO: implement openssl signature')
    else:
        warnings.warn('invalid signature type')
        return
    if result != signature:
        warnings.warn('signature mismatch')
