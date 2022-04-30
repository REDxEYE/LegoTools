from typing import List

from LegoTools.nu20.chunk import Chunk, DummyChunk
from LegoTools.nu20.chunks.gsnh import GSNH
from LegoTools.nu20.chunks.head import Head
from LegoTools.nu20.chunks.ms00 import MS00
from LegoTools.nu20.chunks.ntbl import NTBL
from LegoTools.nu20.chunks.pntr import PNTR
from LegoTools.nu20.chunks.tst0 import TST0
from LegoTools.nu20.chunks.vbib import VBIB
from LegoTools.utils.byte_io_lg import ByteIO


# noinspection PyShadowingNames
class NU20:

    def __init__(self, reader: ByteIO):
        self.reader = reader
        self.version = reader.read_int32()
        reader.read(4)
        self.chunks = []
        while self.reader:
            self.chunks.append(self.read_chunk())

    def read_chunk(self):
        reader = self.reader
        name, size = reader.read_fourcc(), reader.read_uint32()

        if name == 'HEAD':
            return Head(name, size, reader)
        elif name == 'NTBL':
            return NTBL(name, size, reader)
        elif name == 'MS00':
            return MS00(name, size, reader)
        elif name == 'TST0':
            return TST0(name, size, reader)
        elif name == 'PNTR':
            return PNTR(name, size, reader)
        elif name == 'GSNH':
            return GSNH(name, size, reader)
        elif name == 'VBIB':
            return VBIB(name, size, reader)
        else:
            return DummyChunk(name, size, reader)

    def expect_chunk(self, name):
        chunk = self.read_chunk()
        assert chunk.name == name, f'Expected {name}, got {chunk.name}'
        return chunk

    def find_chunk(self, name):
        chunk = list(filter(lambda a: a.name == name, self.chunks))
        if chunk:
            return chunk[0]
        else:
            return None
