from ..chunk import Chunk
from ...utils.byte_io_lg import ByteIO


class VBIB(Chunk):

    def __init__(self, name: str, size: int, reader: ByteIO):
        super().__init__(name, size, reader)
        with reader.new_region('VBIB'):
            self.unk_data = self.reader.read(24)
            self.data = reader.read(size)
