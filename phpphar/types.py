from datetime import datetime
from enum import Flag
from io import FileIO
from typing import Literal
from zlib import crc32

from .constants import _HALT


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

    @staticmethod
    def from_str(s: str):
        if len(s) != 9:
            raise ValueError()
        ret = PharEntryPermission()
        for i in range(len(s)):
            if s[i] != '-':
                ret |= (1 << (8 - i))


class PharEntry:
    name: str
    timestamp: int
    size: int
    compressed_size: int  # calculated on write
    crc32: int
    permissions: PharEntryPermission  # 9-bit
    flags: PharEntryFlag
    metadata: object = None
    content: bytes = None

    @staticmethod
    def from_file(
        name: str, file: FileIO, permissions='rw-r--r--', time: datetime = None,
        compression: Literal['bzip2', 'deflate', 'none'] = 'none',
    ) -> 'PharEntry':
        entry = PharEntry()
        entry.name = name
        with file as f:
            entry.content = f.read()
            if isinstance(entry.content, str):
                entry.content = entry.content.encode('utf-8')
            entry.size = len(entry.content)
        entry.crc32 = crc32(entry.content)
        entry.permissions = PharEntryPermission.from_str(permissions)
        if time == None:
            time = datetime.now()
        entry.timestamp = int(time.timestamp())
        if compression == 'bzip2':
            entry.flags = PharEntryFlag.IS_BZIP2
        elif compression == 'deflate':
            entry.flags = PharEntryFlag.IS_DEFLATE
        elif compression == 'none':
            entry.flags = PharEntryFlag(0)
        return entry


class PharBase:
    stub: str = f'<?php {_HALT} ?>\r\n'
    flags: PharGlobalFlag = PharGlobalFlag.SIGNED  # sha-1 hash
    metadata: object = None
    alias: str = ''
    entries: list[PharEntry] = []
