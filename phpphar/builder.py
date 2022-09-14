from .types import Phar


class PharBuilder:
    def __init__(self, archive: Phar):
        self.archive = archive

    def add_entry(self, name, content):
        pass

    def __bytes__(self):
        return bytes(self.archive)
