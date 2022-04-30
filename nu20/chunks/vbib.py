from ..chunk import Chunk


class VBIB(Chunk):

    def __init__(self, offset: int, name: str, size: int, buffer: bytes):
        super().__init__(offset, name, size, buffer)
        self.unk_data = self.reader.read(32)
