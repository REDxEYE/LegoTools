from ..chunk import Chunk


class Head(Chunk):

    def __init__(self, offset: int, name: str, size: int, buffer: bytes):
        super().__init__(offset, name, size, buffer)
        self.pntr_offset = self.offset + self.reader.tell() + self.reader.read_uint32()
        self.gsnh_offset = self.offset + self.reader.tell() + self.reader.read_uint32()
