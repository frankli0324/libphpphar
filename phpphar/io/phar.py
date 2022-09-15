import hashlib
from io import BytesIO
import warnings
import zlib
import bz2

from phpserialize import serialize, unserialize

import phpphar.types as types
from phpphar.constants import _HALT, _STUB_SFX, _PHAR_VERSION
from phpphar.utils import BZip2Reader, ZlibReader, _readuntil


def read(stream: BytesIO, obj: 'types.PharBase'):
    assert stream.tell() == 0
    obj.stub = _readuntil(stream, _HALT)
    cursor = stream.tell()
    lookahead = stream.read(5)
    for s in _STUB_SFX:
        # `sorted` guarantees that longer patterns are matched first
        if lookahead.startswith(s):
            obj.stub += s
            cursor += len(s)
            break
    stream.seek(cursor)
    read_manifest(stream, obj)
    read_contents(stream, obj)
    verify_signature(stream, obj)


def write(stream: BytesIO, obj: 'types.PharBase'):
    assert stream.tell() == 0
    for s in _STUB_SFX + [b'']:
        if obj.stub.endswith(_HALT + s):
            break
    else:
        url = 'https://www.php.net/manual/en/phar.fileformat.stub.php'
        warnings.warn(f'stub not ended properly. see note in {url}')
    stream.write(obj.stub)
    write_manifest(stream, obj)
    for entry in obj.entries:
        stream.write(entry.__r_content)
        delattr(entry, '__r_content')
    stream.write(hashlib.sha1(stream.getvalue()).digest())
    stream.write(types.PharSignFlag.SHA1.value.to_bytes(4, 'little'))
    stream.write(b'GBMB')


def read_manifest(stream: BytesIO, obj: 'types.PharBase'):
    cursor = stream.tell()
    manifest_len = int.from_bytes(stream.read(4), 'little')
    manifest_end = cursor + manifest_len + 4
    entry_cnt = int.from_bytes(stream.read(4), 'little')
    assert stream.read(2) == _PHAR_VERSION
    obj.flags = types.PharGlobalFlag(int.from_bytes(stream.read(4), 'little'))
    alias_len = int.from_bytes(stream.read(4), 'little')
    obj.alias = stream.read(alias_len).decode('utf-8')
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


def read_entry_manifest(stream: BytesIO, obj: 'types.PharBase'):
    entry = types.PharEntry()
    name_len = int.from_bytes(stream.read(4), 'little')
    entry.name = stream.read(name_len).decode('utf-8')
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


def read_contents(stream: BytesIO, obj: 'types.PharBase'):
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


def verify_signature(stream: BytesIO, obj: 'types.PharBase'):
    if types.PharGlobalFlag.SIGNED not in obj.flags:
        return
    content = stream.getvalue()[:stream.tell()]
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
        # php does level 4 compression, PHP_BZ2_FILTER_DEFAULT_BLOCKSIZE
        r_content = bz2.compress(entry.content, 4)
    elif types.PharEntryFlag.IS_DEFLATE in entry.flags:
        r_content = zlib.compress(entry.content)
    entry.__r_content = r_content
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
