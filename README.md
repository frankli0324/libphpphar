# libphpphar

A port of PHP's Phar class, in pure python

## Installation

`pip install libphpphar` (not available yet)

## Features

- Phar generation with python, no more annoying `phar.readonly = Off`
- uses [libphpserialize](https://github.com/frankli0324/libphpserialize) for metadata serialization

## Example

```python
from phpphar import PharBuilder

class VulnerableObject:
    pass

with open("app.phar", "rb") as f:
    builder = PharBuilder.load(f.read())

builder.add_entry('index.php', '<?php system("whoami");')
builder.set_metadata(VulnerableObject())
# or do it manually
builder.archive.metadata = VulnerableObject()
print(builder.archive.entries)

with open("output.phar", "wb") as f:
    f.write(bytes(builder))
```

## Important

- the code is written and tested under python 3.9+
