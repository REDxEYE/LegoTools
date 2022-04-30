from typing import List

from ..chunk import Chunk
from ...utils.byte_io_lg import ByteIO


class NTBL(Chunk):

    def __init__(self, name: str, size: int, reader: ByteIO):
        super().__init__(name, size, reader)
        with reader.new_region('NTBL'):
            self.string_buffer_size = self.reader.read_uint32()
            self.strings: List[str] = []
            start = self.reader.tell()
            while self.reader.tell() - start < self.string_buffer_size:
                self.strings.append(self.reader.read_ascii_string())
            reader.seek(start + self.string_buffer_size)
            reader.skip(4)

    def __getitem__(self, item):
        assert type(item) is int
        return self.strings[item]
