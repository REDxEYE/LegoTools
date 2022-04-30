from dataclasses import dataclass
from typing import List

from LegoTools.nu20 import Chunk


@dataclass
class TextureMeta:
    width: int
    height: int
    guid: bytes
    unk: bytes


class TST0(Chunk):

    def __init__(self, offset: int, name: str, size: int, buffer: bytes):
        super().__init__(offset, name, size, buffer)
        self.meta: List[TextureMeta] = []
        reader = self.reader

        reader.skip(24)
        while reader:
            width, height = reader.read_fmt('2I')
            guid = reader.read(16)
            unk = reader.read(16)
            self.meta.append(TextureMeta(width, height, guid, unk))
