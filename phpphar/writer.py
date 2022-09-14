from io import BytesIO
import warnings

import phpphar.types as types
from phpphar.constants import _HALT, _STUB_SFX


def write_phar(stream: BytesIO, obj: 'types.Phar'):
    for s in _STUB_SFX + ['']:
        if obj.stub.endswith(_HALT + s):
            break
    else:
        url = 'https://www.php.net/manual/en/phar.fileformat.stub.php'
        warnings.warn(f'stub not ended properly. see note in {url}')
    stream.write(obj.stub)
