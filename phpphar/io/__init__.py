from io import BytesIO
import phpphar.types as types

from .phar import read as read_phar, write as write_phar


class PharIO:
    @staticmethod
    def read(stream: BytesIO, object: types.PharBase):
        raise NotImplementedError()

    @staticmethod
    def write(stream: BytesIO, object: types.PharBase):
        raise NotImplementedError()


class PharIOPhar(PharIO):
    @staticmethod
    def read(stream: BytesIO, object: types.PharBase):
        read_phar(stream, object)

    @staticmethod
    def write(stream: BytesIO, object: types.PharBase):
        write_phar(stream, object)


class PharIOTar(PharIO):
    pass


class PharIOZip(PharIO):
    pass
