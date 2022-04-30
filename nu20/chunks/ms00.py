from typing import List

from ..chunk import Chunk
from ...utils.byte_io_lg import ByteIO


class Material:
    def __init__(self, reader: ByteIO):
        start = reader.tell()
        self.unk = reader.read(56)
        self.unk1 = reader.read_uint32()
        self.id = reader.read_uint32()
        self.mat_info_offset = reader.tell() + reader.read_uint32()
        self.unk3 = reader.read_uint32()
        self.unk4 = reader.read_uint32()
        self.unk5 = reader.read(12)
        self.diffuse_color = reader.read_fmt('4f')
        self.unk7 = reader.read(0x12-2)
        self.texture_id = reader.read_int16()
        self.unk8 = reader.read(0x52)
        self.color = reader.read_fmt('4B')
        self.unk8 = reader.read(0x34)
        self.normal_id = reader.read_int16()
        self.leftover = reader.read(708 - (reader.tell() - start))


class MS00(Chunk):

    def __init__(self, offset: int, name: str, size: int, buffer: bytes):
        super().__init__(offset, name, size, buffer)
        self.materials: List[Material] = []
        material_count = self.reader.read_uint32()

        for _ in range(material_count):
            self.materials.append(Material(self.reader))

    def __getitem__(self, item):
        assert type(item) is int
        return self.materials[item]
