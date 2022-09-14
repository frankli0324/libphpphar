_HALT = b'__HALT_COMPILER();'

_STUB_SFX = sorted([
    b' ?>', b' ?>\r\n', b' ?>\n',
    b'\n?>', b'\n?>\r\n', b'\n?>\n'
], reverse=True, key=lambda x: len(x))

__all__ = ['_HALT', '_STUB_SFX']
