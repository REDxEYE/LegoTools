from ..chunk import Chunk


class PNTR(Chunk):

    def __init__(self, offset: int, name: str, size: int, buffer: bytes):
        super().__init__(offset, name, size, buffer)
        offset_count = self.reader.read_int32()
        self.offsets = []
        for _ in range(offset_count):
            self.offsets.append(offset + self.reader.tell() + self.reader.read_int32())

    def get_offset(self, relative_offset):
        offset = relative_offset - self.offset
        print(offset)
