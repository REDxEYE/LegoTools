from ..chunk import Chunk


class GSNH(Chunk):
    def __init__(self, offset: int, name: str, size: int, buffer: bytes):
        super().__init__(offset, name, size, buffer)
        reader = self.reader
        self.unk, image_count = reader.read_fmt('2I')
        self.image_meta_offset = reader.tell() + reader.read_uint32()
        # with reader.save_current_pos():
        #     reader.seek(image_meta_offset)
        #     self.image_meta_offsets = [offset + reader.tell() + reader.read_int32() for _ in range(image_count)]
        reader.skip(0x28)
        self.mesh_meta_offset = offset + reader.tell() + reader.read_uint32()
        # with reader.save_current_pos():
        #     reader.seek(mesh_meta_offset + 0x14)
        #     part_count = reader.read_int32()
        #     reader.skip(8)
        #     self.part_offsets = [offset + reader.tell() + reader.read_int32() for _ in range(part_count)]
        self.name_offset = offset + reader.tell() + reader.read_int32()
        reader.skip(0x130 - 4)
        self.bone_count = reader.read_int32()
        self.bone_offset = offset + reader.tell() + reader.read_int32()
        reader.skip(32)
        self.layer_count = reader.read_int32()
        self.layer_offset = offset + reader.tell() + reader.read_int32()
