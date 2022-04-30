from ..chunk import Chunk
from ...utils.byte_io_lg import ByteIO


class PNTR(Chunk):

    def __init__(self, name: str, size: int, reader: ByteIO):
        super().__init__(name, size, reader)
        with reader.new_region('PNTR'):
            offset_count = self.reader.read_int32()
            self.offsets = []
            for _ in range(offset_count):
                self.offsets.append(self.reader.tell() + self.reader.read_int32())

    def get_offset(self, relative_offset):
        offset = relative_offset - self.offset
        print(offset)
