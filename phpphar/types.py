from enum import Flag
from io import BytesIO

from .constants import _HALT
from .reader import read_manifest, read_contents, verify_signature
from .writer import write_phar


class PharGlobalFlag(Flag):
    SIGNED = 0x00010000
    HAS_DEFLATE = 0x00001000
    HAS_BZIP2 = 0x00002000


class PharEntryFlag(Flag):
    # file permissions are calculated independently
    IS_DEFLATE = 0x00001000
    IS_BZIP2 = 0x00002000


class PharSignFlag(Flag):
    MD5 = 0x0001
    SHA1 = 0x0002
    SHA256 = 0x0003
    SHA512 = 0x0004
    OPENSSL = 0x0010


class PharEntryPermission(int):
    def __repr__(self) -> str:
        perms = list('rwxrwxrwx')
        for i in range(9):
            if self >> i & 1 == 0:
                perms[8 - i] = '-'
        return ''.join(perms)


class PharEntry:
    name: str
    timestamp: int
    size: int
    compressed_size: int
    crc32: bytes
    permissions: PharEntryPermission  # 9-bit
    flags: PharEntryFlag
    metadata: object = None
    content = None


class Phar:
    stub: str = f'<?php {_HALT}'
    flags: PharGlobalFlag = PharGlobalFlag.SIGNED  # sha-1 hash
    metadata: object = None
    alias: str = ''
    entries: list[PharEntry] = []

    def __bytes__(self):
        stream = BytesIO()
        write_phar(stream, self)
        stream.getbuffer().tobytes()

    @staticmethod
    def from_bytes(data: bytes) -> 'Phar':
        obj = Phar()
        stream = BytesIO(data)
        read_manifest(stream, obj)
        read_contents(stream, obj)
        verify_signature(stream, obj)
        return obj
