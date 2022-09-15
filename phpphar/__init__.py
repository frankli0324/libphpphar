from io import BytesIO
from .types import PharBase, PharEntry
from .io import PharIO, PharIOPhar, PharIOTar, PharIOZip


class Phar(PharBase):
    def __init__(self, io_cls=PharIOPhar):
        super().__init__()
        self.io_cls = io_cls

    def __bytes__(self):
        output = BytesIO()
        self.io_cls.write(output, self)
        return output.getvalue()

    @staticmethod
    def from_bytes(buffer, io_cls=PharIOPhar):
        ret = Phar()
        with BytesIO(buffer) as stream:
            io_cls.read(stream, ret)
        return ret


__all__ = [
    'Phar', 'PharEntry',
    'PharIO', 'PharIOPhar', 'PharIOTar', 'PharIOZip'
]
