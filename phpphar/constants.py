_HALT = b'__HALT_COMPILER();'

_STUB_SFX = sorted([
    b' ?>', b' ?>\r\n', b' ?>\n',
    b'\n?>', b'\n?>\r\n', b'\n?>\n'
], reverse=True, key=lambda x: len(x))

_PHAR_VERSION = b'\x11\x00'

__all__ = ['_HALT', '_STUB_SFX', '_PHAR_VERSION']
