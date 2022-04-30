import random
from pathlib import Path

import numpy as np

from LegoTools.ghg import GHG
import bpy
from mathutils import Vector, Matrix


def get_material(mat_name, model_ob):
    md = model_ob.data
    mat = bpy.data.materials.get(mat_name, None)
    if mat:
        if md.materials.get(mat.name, None):
            for i, material in enumerate(md.materials):
                if material == mat:
                    return i
        else:
            md.materials.append(mat)
            return len(md.materials) - 1
    else:
        mat = bpy.data.materials.new(mat_name)
        mat.diffuse_color = [random.uniform(.4, 1) for _ in range(3)] + [1.0]
        md.materials.append(mat)
        return len(md.materials) - 1


if __name__ == '__main__':
    path = Path(r"D:\SteamLibrary\steamapps\common\Lego Star Wars Saga\dump\CHARS\BARMAN\BARMAN_PC.GHG")
    with open(path, 'rb') as f:
        a = GHG(f.read())
        a.reader.export_as_010editor_bookmarks('test.csv')
        exit(0)
        print(a)

        armature = bpy.data.armatures.new(f"{path.stem}_ARM_DATA")
        armature_obj = bpy.data.objects.new(f"{path.stem}_ARM", armature)
        armature_obj.show_in_front = True
        bpy.context.scene.collection.objects.link(armature_obj)

        armature_obj.select_set(True)
        bpy.context.view_layer.objects.active = armature_obj

        bpy.ops.object.mode_set(mode='EDIT')
        bl_bones = []
        matrices = []
        for bone in a.bones:
            bl_bone = armature.edit_bones.new(bone.name)
            bl_bones.append(bl_bone)
        for bl_bone, s_bone in zip(bl_bones, a.bones):
            if s_bone.parent_id != -1:
                bl_parent = bl_bones[s_bone.parent_id]
                bl_bone.parent = bl_parent
            bl_bone.tail = (Vector([0.01, 0, 0])) + bl_bone.head
        bpy.ops.object.mode_set(mode='POSE')
        for se_bone in a.bones:
            bl_bone = armature_obj.pose.bones.get(se_bone.name[-63:])
            mat = Matrix(se_bone.mat)
            bl_bone.matrix_basis.identity()
            bl_bone.matrix = bl_bone.parent.matrix @ mat if bl_bone.parent else mat
            matrices.append(bl_bone.matrix)
            # bl_bone.matrix = mat
        bpy.ops.pose.armature_apply()
        bpy.ops.object.mode_set(mode='OBJECT')
        del se_bone, bl_bone, s_bone, bl_parent, mat
        global_part_offset = 0
        for layer_id, layer in enumerate(a.layers):
            print(layer.name)
            for part in layer.bone_part_pairs:
                print('\t', part)
                meshes = a.meshes[global_part_offset:global_part_offset + part.part_count]
                for mesh_id, mesh in enumerate(meshes):
                    print('\t', mesh_id)
                    mesh_name = f'{layer.name}_{part.pointer}_{mesh_id}'
                    mesh_data = bpy.data.meshes.new(f'{mesh_name}_MESH')
                    mesh_obj = bpy.data.objects.new(mesh_name, mesh_data)
                    indices = []
                    for idx in range(len(mesh.indices) - 2):
                        tmp = mesh.indices[idx:idx + 3].tolist()
                        if tmp[0] == tmp[1] or tmp[1] == tmp[2]:
                            continue
                        indices.append(tmp)
                    del tmp, idx
                    if mesh.vertex_size == 40:
                        dtype = np.dtype([
                            ('pos', np.float32, 3),
                            ('unk1', np.int32, 3),
                            ('uv', np.float32, 2),
                            ('weight', np.uint8, 4),
                            ('bone_id', np.int8, 4),
                        ])
                    elif mesh.vertex_size == 44:
                        dtype = np.dtype([
                            ('pos', np.float32, 3),
                            ('unk1', np.int32, 4),
                            ('uv', np.float32, 2),
                            ('weight', np.uint8, 4),
                            ('bone_id', np.int8, 4),
                        ])
                    elif mesh.vertex_size == 36:
                        dtype = np.dtype([
                            ('pos', np.float32, 3),
                            ('unk1', np.int32, 4),
                            ('uv', np.float32, 2),
                        ])
                    elif mesh.vertex_size == 32:
                        dtype = np.dtype([
                            ('pos', np.float32, 3),
                            ('unk1', np.int32, 3),
                            ('uv', np.float32, 2),
                        ])
                    else:
                        raise NotImplementedError(f'Unsupported mesh vertex size: {mesh.vertex_size}')

                    with open(f'dump/vbuf_{layer.name}_{global_part_offset + mesh_id}_{mesh.vertex_size}.bin',
                              'wb') as f:
                        f.write(mesh.vertex_buffer)
                    vertices = np.frombuffer(mesh.vertex_buffer, dtype=dtype)

                    mesh_data.from_pydata(vertices['pos'].tolist(), [], indices)
                    mesh_data.update()

                    material_id = part.materials[mesh_id]
                    material = a.materials[material_id]
                    get_material(f'material_{material_id}', mesh_obj)

                    vertex_indices = np.zeros((len(mesh_data.loops, )), dtype=np.uint32)
                    mesh_data.loops.foreach_get('vertex_index', vertex_indices)
                    uv_data = mesh_data.uv_layers.new(name=f'UV')
                    uv_layer_data = vertices['uv'].copy()
                    uv_layer_data[:, 1] = (1 - uv_layer_data[:, 1]) - 1
                    uv_data.data.foreach_set('uv', uv_layer_data[vertex_indices].flatten())

                    weight_groups = {bone.name: mesh_obj.vertex_groups.new(name=bone.name) for bone in a.bones}
                    if part.bone_id == -1:
                        for n, vertex in enumerate(vertices):
                            for (bone_index, weight) in zip(vertex['bone_id'][:2], vertex['weight'][:2]):
                                if weight > 0 and weight != 0xFF:
                                    bone_name = a.bones[bone_index].name
                                    weight_groups[bone_name].add([n], weight / 255, 'REPLACE')

                        modifier = mesh_obj.modifiers.new(type="ARMATURE", name="Armature")
                        modifier.object = armature_obj
                        mesh_obj.parent = armature_obj

                    if part.bone_id != -1:
                        mesh_obj.parent = armature_obj
                        mesh_obj.parent_type = 'BONE'
                        bone = armature_obj.data.bones[part.bone_id]
                        mesh_obj.parent_bone = bone.name
                        mpi = mesh_obj.matrix_parent_inverse
                        ti = Matrix.Translation([0, bone.length, 0]).inverted()
                        mesh_obj.matrix_parent_inverse = mpi @ ti

                    bpy.context.scene.collection.objects.link(mesh_obj)
                global_part_offset += part.part_count

        for i, texture in enumerate(a.textures):
            with open(f'dump/texture_{i}.dds', 'wb') as f:
                f.write(texture.buffer)
bpy.ops.wm.save_as_mainfile(filepath=r"F:\PYTHON_STUFF\LegoToolsAddon\models.blend")
