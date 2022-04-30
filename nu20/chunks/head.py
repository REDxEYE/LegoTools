from ..chunk import Chunk
from ...utils.byte_io_lg import ByteIO


class Head(Chunk):

    def __init__(self, name: str, size: int, reader: ByteIO):
        super().__init__(name, size, reader)
        with reader.new_region('HEAD'):
            self.pntr_offset = self.reader.tell() + self.reader.read_uint32()
            self.gsnh_offset = self.reader.tell() + self.reader.read_uint32()
