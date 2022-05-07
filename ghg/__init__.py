import io
from dataclasses import dataclass
from enum import IntEnum
from typing import List

import numpy as np

from LegoTools.nu20 import NU20
from LegoTools.nu20.chunks.gsnh import GSNH
from LegoTools.nu20.chunks.ms00 import MS00
from LegoTools.utils.byte_io_lg import ByteIO


class GHGType(IntEnum):
    BATMAN = 0
    STARWARS = 1


class PixelFormat(IntEnum):
    DXT1 = 12
    DXT5 = 15


@dataclass
class Texture:
    width: int
    height: int
    mips: int
    pfmt: PixelFormat
    flags: int
    size: int
    buffer: bytes


@dataclass
class Mesh:
    vertex_buffer: bytes
    vertex_size: int
    indices: np.ndarray


@dataclass
class Bone:
    name: str
    mat: np.ndarray
    parent_id: int


@dataclass
class BonePartPair:
    pointer: int
    bone_id: int
    part_count: int
    materials: List[int]


@dataclass
class Layer:
    name: str
    p1: int
    p2: int
    p3: int
    p4: int
    bone_part_pairs: List[BonePartPair]


class GHG:

    def __init__(self, buffer: bytes):
        self.type = GHGType.STARWARS
        self.textures = []
        reader = self.reader = ByteIO(buffer)

        nu20_offset = reader.read_uint32()
        if nu20_offset == 0x3032554E:
            raise NotImplementedError()
            # nu20_offset = 0
            # nu_size = -reader.read_int32()
            # self.nu20 = NU20(nu20_offset, reader.read(nu_size - 8))
            pass
        else:
            self.type = GHGType.STARWARS
            texture_count = reader.read_int16()
            for _ in range(texture_count):
                width, height, mips, pfmt, flags, size = reader.read_fmt('6I')
                data = reader.read(size)
                self.textures.append(Texture(width, height, mips, PixelFormat(pfmt), flags, size, data))
            del width, height, mips, pfmt, flags, size, data
            vertex_buffers_count = reader.read_uint16()
            vertex_buffers = [reader.read(reader.read_uint32()) for _ in range(vertex_buffers_count)]
            indices_buffers_count = reader.read_uint16()
            indices_buffers = [np.frombuffer(reader.read(reader.read_uint32()), np.uint16) for _ in
                               range(indices_buffers_count)]
            reader.seek(nu20_offset)
            reader.read_uint32()
            magic = reader.read_uint32()
            assert magic == 0x3032554E, f'Invalid magic, expected 0x3032554E, got {magic}'
            reader.read_int32()
            self.nu20 = NU20(reader)
            del magic, texture_count, nu20_offset, indices_buffers_count, vertex_buffers_count

        # for i, texture in enumerate(self.textures):
        #     with open(f'tmp_{i}.dds', 'wb') as f:
        #         f.write(texture.buffer)

        gsnh: GSNH = self.nu20.find_chunk('GSNH')
        ms00: MS00 = self.nu20.find_chunk('MS00')
        self.materials = ms00.materials
        reader.seek(gsnh.name_offset)
        self.scene_name = reader.read_ascii_string()

        reader.seek(gsnh.mesh_meta_offset + 0x14)
        with reader.new_region('PartsOffsets'):
            part_count = reader.read_uint32()
            reader.skip(8)
            part_offsets = [reader.tell() + reader.read_int32() for _ in range(part_count)]

        self.meshes: List[Mesh] = []
        for part_id, part_offset in enumerate(part_offsets):
            reader.seek(part_offset)
            with reader.new_region(f'PartsInfo::Part_{part_id}', 'Part', 0x38):
                assert reader.read_uint32() == 6
                indices_count = reader.read_uint32() + 2
                vertex_size = reader.read_int16()
                reader.skip(0xA)
                vertex_offset, vertex_count, indices_offset = reader.read_fmt('3I')
                indices_buffer_id, vertices_buffer_id = reader.read_fmt('2I')
                reader.skip(0xF)
                indices = indices_buffers[indices_buffer_id][indices_offset:indices_offset + indices_count]
                offset_vertex_size = vertex_offset * vertex_size
                vertices_buffer = vertex_buffers[vertices_buffer_id][
                                  offset_vertex_size:offset_vertex_size + vertex_count * vertex_size]
            mesh = Mesh(vertices_buffer, vertex_size, indices)
            self.meshes.append(mesh)
            del (indices_count, vertex_size, vertex_offset, vertex_count,
                 indices_offset, indices_buffer_id, vertices_buffer_id,
                 indices, vertices_buffer, mesh)
        del part_offset, part_count

        reader.seek(gsnh.bone_offset)
        self.bones = []
        with reader.new_region('Bones') as reg:
            for bone in range(gsnh.bone_count):
                with reg.sub_region(f'Bones::Bone_{bone}', 'Bone', 0x60):
                    mat = np.frombuffer(reader.read(64), np.float32).reshape((4, 4)).T
                    reader.skip(12)
                    name_offset = reader.tell() + reader.read_int32()
                    with reader.save_current_pos():
                        reader.seek(name_offset)
                        bone_name = reader.read_ascii_string()
                    parent_id = reader.read_int8()
                    reader.skip(3 + 12)
                self.bones.append(Bone(bone_name, mat, parent_id))
                del name_offset, parent_id, mat, bone_name
        with reader.new_region('BoneMatrices'):
            for bone_id, bone in enumerate(self.bones):
                bone.mat = np.frombuffer(reader.read(64), np.float32).reshape((4, 4)).T

        reader.seek(gsnh.layer_offset)
        self.layers: List[Layer] = []
        with reader.new_region('Layers') as reg:
            for layer_id in range(gsnh.layer_count):
                with reg.sub_region(f'Layers::Layer_{layer_id}', 'Layer', 0x14):
                    name_offset = reader.tell() + reader.read_int32()
                    with reader.save_current_pos():
                        reader.seek(name_offset)
                        layer_name = reader.read_ascii_string()
                    p1 = reader.read_int32() if reader.peek_int32() == 0 else reader.tell() + reader.read_int32()
                    p2 = reader.read_int32() if reader.peek_int32() == 0 else reader.tell() + reader.read_int32()
                    p3 = reader.read_int32() if reader.peek_int32() == 0 else reader.tell() + reader.read_int32()
                    p4 = reader.read_int32() if reader.peek_int32() == 0 else reader.tell() + reader.read_int32()
                self.layers.append(Layer(layer_name, p1, p2, p3, p4, []))
                del p1, p2, p3, p4, layer_name, name_offset

        for n, layer in enumerate(self.layers):
            if layer.p1:
                reader.seek(layer.p1)
                with reader.new_region(f'Layer_{n}::P1::BoneOffsets', 'int', sizeof=4):
                    bone_offsets = {}
                    for bone_id, _ in enumerate(self.bones):
                        offset = reader.read_int32()
                        if offset:
                            bone_offsets[bone_id] = reader.tell() - 4 + offset
                for bone_id, offset in bone_offsets.items():
                    reader.seek(offset)
                    with reader.new_region(f'Layer_{n}::P1::Unk_{bone_id}'):
                        reader.skip(8)
                        data_offset = reader.tell() + reader.read_int32()
                    reader.seek(data_offset)
                    with reader.new_region(f'Layer_{n}::P1::Unk_{bone_id}::Unk2'):
                        reader.skip(176)
                        data_offset = reader.tell() + reader.read_int32()
                        name_offset = reader.tell() + reader.read_int32()
                        with reader.save_current_pos():
                            reader.seek(name_offset)
                            name = reader.read_ascii_string()
                            print(f'unk2 name {name}')
                    reader.seek(data_offset)
                    with reader.new_region(f'Layer_{n}::P1::Unk_{bone_id}::Unk2::PartInfo', 'LayerPartInfo', 0xC):
                        part_count = reader.read_int32()
                        data_offset = reader.tell() + reader.read_int32()
                        reader.skip(4)
                    reader.seek(data_offset)
                    with reader.new_region(f'Layer_{n}::P1::Unk_{bone_id}::PartInfo::MaterialList', 'int', 4):
                        materials = [reader.read_int32() for _ in range(part_count)]
                    layer.bone_part_pairs.append(BonePartPair(2, bone_id, part_count, materials))

            if layer.p2:
                reader.seek(layer.p2)
                with reader.new_region(f'Layer_{n}::P2'):
                    reader.skip(8)
                    data_offset = reader.tell() + reader.read_int32()
                reader.seek(data_offset)
                with reader.new_region(f'Layer_{n}::P2::Unk'):
                    reader.skip(0xB0)
                    data_offset = reader.tell() + reader.read_int32()
                reader.seek(data_offset)
                with reader.new_region(f'Layer_{n}::P2::Unk::PartInfo'):
                    part_count = reader.read_int32()
                    data_offset = reader.tell() + reader.read_int32()
                reader.seek(data_offset)
                with reader.new_region(f'Layer_{n}::P2::Unk::PartInfo::MaterialList'):
                    materials = [reader.read_int32() for _ in range(part_count)]
                layer.bone_part_pairs.append(BonePartPair(1, -1, part_count, materials))

            if layer.p3:
                reader.seek(layer.p3)
                with reader.new_region(f'Layer_{n}::P3::BoneOffsets', 'int', sizeof=4):
                    bone_offsets = {}
                    for bone_id, _ in enumerate(self.bones):
                        offset = reader.read_int32()
                        if offset:
                            bone_offsets[bone_id] = reader.tell() - 4 + offset
                for bone_id, offset in bone_offsets.items():
                    reader.seek(offset)
                    with reader.new_region(f'Layer_{n}::P3::Unk_{bone_id}'):
                        reader.skip(8)
                        data_offset = reader.tell() + reader.read_int32()
                    reader.seek(data_offset)
                    with reader.new_region(f'Layer_{n}::P3::Unk_{bone_id}::Unk2'):
                        reader.skip(176)
                        data_offset = reader.tell() + reader.read_int32()
                        name_offset = reader.tell() + reader.read_int32()
                        with reader.save_current_pos():
                            reader.seek(name_offset)
                            name = reader.read_ascii_string()
                            print(f'unk2 name {name}')
                    reader.seek(data_offset)
                    with reader.new_region(f'Layer_{n}::P3::Unk_{bone_id}::Unk2::PartInfo', 'LayerPartInfo', 0xC):
                        part_count = reader.read_int32()
                        data_offset = reader.tell() + reader.read_int32()
                    reader.seek(data_offset)
                    with reader.new_region(f'Layer_{n}::P3::Unk_{bone_id}::PartInfo::MaterialList', 'int', 4):
                        materials = [reader.read_int32() for _ in range(part_count)]
                    layer.bone_part_pairs.append(BonePartPair(2, bone_id, part_count, materials))

            if layer.p4:
                reader.seek(layer.p4)
                with reader.new_region(f'Layer_{n}::P4'):
                    reader.skip(8)
                    data_offset = reader.tell() + reader.read_int32()
                reader.seek(data_offset)
                with reader.new_region(f'Layer_{n}::P4::Unk'):
                    reader.skip(0xB0)
                    data_offset = reader.tell() + reader.read_int32()
                reader.seek(data_offset)
                with reader.new_region(f'Layer_{n}::P4::Unk::PartInfo'):
                    part_count = reader.read_int32()
                    data_offset = reader.tell() + reader.read_int32()
                reader.seek(data_offset)
                with reader.new_region(f'Layer_{n}::P4::Unk::PartInfo::MaterialList'):
                    materials = [reader.read_int32() for _ in range(part_count)]
                layer.bone_part_pairs.append(BonePartPair(1, -1, part_count, materials))
