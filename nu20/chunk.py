from LegoTools.utils.byte_io_lg import ByteIO


class Chunk:

    def __init__(self, offset: int, name: str, size: int, buffer: bytes):
        self.offset = offset
        self.name = name
        self.size = size
        self.reader = ByteIO(buffer)

    def __str__(self):
        return f"<Chunk \"{self.name}\" at {self.offset} size:{self.size}>"
