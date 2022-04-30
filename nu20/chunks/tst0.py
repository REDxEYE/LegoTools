from dataclasses import dataclass
from typing import List

from LegoTools.nu20 import Chunk
from LegoTools.utils.byte_io_lg import ByteIO


@dataclass
class TextureMeta:
    width: int
    height: int
    guid: bytes
    unk: bytes


class TST0(Chunk):

    def __init__(self, name: str, size: int, reader: ByteIO):
        super().__init__(name, size, reader)
        self.meta: List[TextureMeta] = []
        reader = self.reader
        with reader.new_region('TST0') as reg:
            reader.skip(24)
            while reader.tell() < self.offset + size - 8:
                with reg.sub_region('TST0::TextureMeta'):
                    width, height = reader.read_fmt('2I')
                    guid = reader.read(16)
                    unk = reader.read(16)
                self.meta.append(TextureMeta(width, height, guid, unk))
