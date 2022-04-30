from LegoTools.utils.byte_io_lg import ByteIO


class Chunk:

    def __init__(self, name: str, size: int, reader: ByteIO):
        self.name = name
        self.size = size
        self.reader = reader
        self.offset = self.reader.tell()

    def __str__(self):
        return f"<Chunk \"{self.name}\" at {self.offset} size:{self.size}>"


class DummyChunk(Chunk):
    def __init__(self, name: str, size: int, reader: ByteIO):
        super().__init__(name, size, reader)
        self.data = reader.read(size - 8)
