from typing import List

from ..chunk import Chunk


class NTBL(Chunk):

    def __init__(self, offset: int, name: str, size: int, buffer: bytes):
        super().__init__(offset, name, size, buffer)
        self.string_buffer_size = self.reader.read_uint32()
        self.strings: List[str] = []
        start = self.reader.tell()
        while self.reader.tell() - start < self.string_buffer_size:
            self.strings.append(self.reader.read_ascii_string())

    def __getitem__(self, item):
        assert type(item) is int
        return self.strings[item]
