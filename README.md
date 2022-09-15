# libphpphar

A port of PHP's Phar class, in pure python

## Installation

`pip install libphpphar` (not available yet)

## Features

- Phar generation with python, no more annoying `phar.readonly = Off`
- uses [libphpserialize](https://github.com/frankli0324/libphpserialize) for metadata serialization

## Example

```python
from datetime import datetime
from io import BytesIO
from phpphar import Phar, PharIOPhar
from phpserialize import PHP_Class

# for (un)serializing the metadatas
class VulnerableObject(PHP_Class):
    pass

with open("app.phar", "rb") as f:
    original = f.read()

archive: Phar = Phar.from_bytes(original)
# simply `archive = Phar()` if you want to start from scratch
print(archive.metadata)
for entry in archive.entries:
    print(f'{entry.permissions}\t{entry.size}\t{datetime.fromtimestamp(entry.timestamp)}\t{entry.name}')
output = bytes(archive)
assert original == output
```

## Important

- the code is written and tested under python 3.9+
