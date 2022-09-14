import enum
from io import BytesIO

from .constants import _HALT
from .writer import write_phar


class PharGlobalFlag(enum.Flag):
    SIGNED = 0x00010000
    HAS_DEFLATE = 0x00001000
    HAS_BZIP2 = 0x00002000


class PharEntry:
    pass


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
