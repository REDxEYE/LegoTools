from inc_noesis import *
import noesis
import rapi


def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''

    handle = noesis.register("LEGO TTGames Mesh (*pc.ghg)", ".ghg")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1


def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    bs = NoeBitStream(data)
    tmp = bs.readInt()
    if tmp == 0x3032554e:  # NU20 #Batman
        return 1

    bs.seek(tmp, NOESEEK_REL)
    tmp = bs.readInt()
    if tmp == 0x3032554e:  # NU20 #Star Wars
        return 1

    return 0


def noepyLoadModel(data, mdlList):
    bs = NoeBitStream(data)

    ctx = rapi.rpgCreateContext()
    stack = []
    textures = []
    materials = []

    NU20 = bs.readInt()
    if NU20 == 0x3032554e:  # NU20 #Batman
        print("NU20 first")
    else:
        print("NU20 @ 0x%x" % NU20)
        numberImg = bs.readShort()
        print("numberImg %d" % numberImg)
        bs.seek(NU20 + 4, NOESEEK_ABS)
        bs.seek(0x4, NOESEEK_REL)

    bs.seek(0xc, NOESEEK_REL)

    # HEAD
    four_cc = bs.readInt()
    chunk_size = bs.readInt()
    abs_offset_pntr = bs.tell() + bs.readInt()
    offset_gsnh = bs.readInt()
    abs_offset_gsnh = bs.tell() + offset_gsnh

    # NTBL
    four_cc = bs.readInt()
    chunk_size = bs.readInt()
    bs.seek(chunk_size - 8, NOESEEK_REL)

    four_cc = bs.readInt()
    if (four_cc == 1178948180):  # TREF
        chunk_size = bs.readInt()
        bs.seek(chunk_size - 8, NOESEEK_REL)
        four_cc = bs.readInt()

    if (four_cc == 810832724):  # TST0
        chunk_size = bs.readInt()
        bs.seek(chunk_size - 8, NOESEEK_REL)
        four_cc = bs.readInt()

    # MS00 - Materials
    print("MS00 @ 0x%x" % (bs.tell() - 4))
    # four_cc = bs.readInt()
    chunk_size = bs.readInt()
    number_materials = bs.readInt()
    bs.seek(4, NOESEEK_REL)  # 0
    for i in range(0, number_materials):
        material = NoeMaterial("mat%03i" % i, "")  # create a material
        bs.seek(0x38, NOESEEK_REL)  #
        mat_id = bs.readInt()
        bs.seek(0x18, NOESEEK_REL)  #
        material.setDiffuseColor(NoeVec4([bs.readFloat(), bs.readFloat(), bs.readFloat(), bs.readFloat()]))
        bs.seek(0x10, NOESEEK_REL)  #
        tex_id = bs.readShort()
        if (tex_id != -1):
            material.setTexture("tex%03i" % tex_id)
        bs.seek(0x52, NOESEEK_REL)  #
        color_rbga = bs.readBytes(4)
        #        material.setDiffuseColor(NoeVec4([color_rbga[0]/255, color_rbga[1]/255, color_rbga[2]/255, color_rbga[3]/255]))
        bs.seek(0x1F8, NOESEEK_REL)  #
        materials.append(material)

    bs.seek(abs_offset_gsnh - 12, NOESEEK_ABS)
    # GSNH
    print("GSNH @ 0x%x" % bs.tell())
    four_cc = bs.readInt()
    chunk_size = bs.readInt()
    bs.readInt()
    number_images = bs.readInt()
    print("NumberImages %d" % number_images)
    abs_offset_images_meta = bs.tell() + bs.readInt()
    bs.seek(0x28, NOESEEK_REL)
    abs_offset_mesh_meta = bs.readInt() - 4 + bs.tell()
    bs.seek(0x130, NOESEEK_REL)
    number_bones = bs.readInt()
    abs_offset_bones = bs.readInt() - 4 + bs.tell()
    print("NumberBones %d" % number_bones)
    bs.readInt()
    bs.readInt()
    bs.seek(24, NOESEEK_REL)
    number_layer = bs.readInt()
    abs_offset_layer = bs.readInt() - 4 + bs.tell()
    print("NumberLayer %d" % number_layer)

    # goto image meta
    bs.seek(abs_offset_images_meta, NOESEEK_ABS)
    size = 0
    if NU20 == 0x3032554e:  # Batman
        imageMetas = []
        for i in range(0, number_images):
            tmp = bs.readInt()
            stack.append(bs.tell())
            bs.seek(tmp - 4, NOESEEK_REL)
            width = bs.readInt()
            height = bs.readInt()
            bs.seek(0x10, NOESEEK_REL)
            bs.seek(0x2c, NOESEEK_REL)
            size = bs.readInt()
            print("Image{0}: width = {1:4d}; height = {2:4d}; size = {3:8d}".format(i, width, height, size))
            imageMetas.append(ImageMeta(width, height, size))
            bs.seek(stack.pop(), NOESEEK_ABS)
        bs.seek(abs_offset_pntr - 8, NOESEEK_ABS)  # goto PNTR
        # print("1 0x%x" % bs.tell())
        four_cc = bs.readInt()
        # print("2 0x%x" % bs.tell())
        chunk_size = bs.readInt()
        print("3 0x%x" % bs.tell())
        bs.seek(chunk_size - 4, NOESEEK_REL)  # goto EndOfPNTR
        print("4 0x%x" % bs.tell())
        for i in range(0, number_images):
            data = bs.readBytes(imageMetas[i].size)
            texture = rapi.loadTexByHandler(data, ".dds")  # NoeTexture(str(i), width, height, data, texFmt)
            texture.name = "tex%03i" % i
            textures.append(texture)
        # bs.seek(size, NOESEEK_REL)
        print("5 0x%x" % bs.tell())
    else:
        numberRealImages = 0
        for i in range(0, number_images):
            tmp = bs.readInt()
            stack.append(bs.tell())
            bs.seek(tmp - 4, NOESEEK_REL)
            width = bs.readInt()
            height = bs.readInt()
            print("Image{0}: width = {1:4d}; height = {2:4d}".format(i, width, height))
            if width != 0 and height != 0: numberRealImages += 1
            bs.seek(stack.pop(), NOESEEK_ABS)
        bs.seek(6, NOESEEK_ABS)  # goto beginOfFile + 6
        for i in range(0, numberRealImages):
            pos = bs.tell()
            width = bs.readInt()
            height = bs.readInt()
            bs.readInt()
            bs.readInt()
            bs.readInt()
            size = bs.readInt()
            print("Image{0} @ {1:8x}: width = {2:4d}; height = {3:4d}".format(i, pos, width, height))
            data = bs.readBytes(size)
            texture = rapi.loadTexByHandler(data, ".dds")  # NoeTexture(str(i), width, height, data, texFmt)
            texture.name = "tex%03i" % i
            textures.append(texture)
    #            bs.seek(size, NOESEEK_REL)
    # End DDS

    vertexLists = []
    numberVertexLists = bs.readShort()
    for i in range(0, numberVertexLists):
        size = bs.readInt()
        vertexLists.append(bs.readBytes(size))

    indexLists = []
    numberIndices = bs.readShort()
    for i in range(0, numberIndices):
        size = bs.readInt()
        indexLists.append(bs.readBytes(size))

    bs.seek(abs_offset_mesh_meta, NOESEEK_ABS)
    bs.seek(0x14, NOESEEK_REL)
    numberParts = bs.readInt()
    print("NumberParts %d" % numberParts)
    bs.seek(0x08, NOESEEK_REL)
    partPos = bs.tell()
    bytesForPositions = []
    stride = []
    bytesForIndexBuffer = []
    numIdx = []
    for i in range(0, numberParts):
        offsetPart = bs.readInt()
        bs.seek(offsetPart - 4, NOESEEK_REL)
        bs.readInt() // 6
        numberIndices = bs.readInt() + 2
        sizeVertex = bs.readShort()
        bs.seek(0x0a, NOESEEK_REL)
        offsetVertex = bs.readInt()
        numberVertex = bs.readInt()
        offsetIndices = bs.readInt()
        indexList = bs.readInt()
        vertexList = bs.readInt()

        bytesForPositions.append(
            vertexLists[vertexList][offsetVertex * sizeVertex:offsetVertex * sizeVertex + numberVertex * sizeVertex])
        stride.append(sizeVertex)
        bytesForIndexBuffer.append(indexLists[indexList][offsetIndices * 2:offsetIndices * 2 + numberIndices * 2])
        numIdx.append(numberIndices)
        partPos += 4
        bs.seek(partPos, NOESEEK_ABS)

    bs.seek(abs_offset_layer, NOESEEK_ABS)
    layers = []
    for i in range(0, number_layer):
        layer = Layer(i)
        absOffsetText = bs.readInt() - 4 + bs.tell()
        tmp = bs.readInt()
        if (tmp != 0):
            layer.p1 = bs.tell() + tmp - 4
        tmp = bs.readInt()
        if (tmp != 0):
            layer.p2 = bs.tell() + tmp - 4
        tmp = bs.readInt()
        if (tmp != 0):
            layer.p3 = bs.tell() + tmp - 4
        tmp = bs.readInt()
        if (tmp != 0):
            layer.p4 = bs.tell() + tmp - 4
        layers.append(layer)

    for layer in (layers):
        if (layer.p1 != 0):
            bs.seek(layer.p1, NOESEEK_ABS)
            for j in range(0, number_bones):
                tmp = bs.readInt()
                if (tmp != 0):
                    stack.append(bs.tell())
                    bs.seek(tmp - 4, NOESEEK_REL)
                    bs.seek(8, NOESEEK_REL)
                    bs.seek(bs.readInt() - 4, NOESEEK_REL)  # --> matrix
                    bs.seek(0xB0, NOESEEK_REL)
                    bs.seek(bs.readInt() - 4, NOESEEK_REL)  # --> number of parts
                    parts = bs.readInt()
                    bs.seek(bs.readInt() - 4, NOESEEK_REL)  # --> materials
                    partMaterials = []
                    for p in range(0, parts):
                        partMaterials.append(bs.readInt())
                    partMaterials = list(reversed(partMaterials))
                    bs.seek(stack.pop(), NOESEEK_ABS)
                    bonePartPair = BonePartPair(0, j, parts, partMaterials)
                    layer.bonePartPairs.append(bonePartPair)

        if (layer.p2 != 0):
            bs.seek(layer.p2, NOESEEK_ABS)
            bs.seek(8, NOESEEK_REL)
            bs.seek(bs.readInt() - 4, NOESEEK_REL)  # --> matrix
            bs.seek(0xB0, NOESEEK_REL)
            bs.seek(bs.readInt() - 4, NOESEEK_REL)  # --> number of parts
            parts = bs.readInt()
            bs.seek(bs.readInt() - 4, NOESEEK_REL)  # --> materials
            partMaterials = []
            for p in range(0, parts):
                partMaterials.append(bs.readInt())
            partMaterials = list(reversed(partMaterials))
            # bs.seek(stack.pop(), NOESEEK_ABS)
            bonePartPair = BonePartPair(1, -1, parts, partMaterials)
            layer.bonePartPairs.append(bonePartPair)

        if (layer.p3 != 0):
            bs.seek(layer.p3, NOESEEK_ABS)
            for j in range(0, number_bones):
                # parts = 0
                tmp = bs.readInt()
                if (tmp != 0):
                    stack.append(bs.tell())
                    bs.seek(tmp - 4, NOESEEK_REL)
                    bs.seek(8, NOESEEK_REL)
                    bs.seek(bs.readInt() - 4, NOESEEK_REL)  # --> matrix
                    bs.seek(0xB0, NOESEEK_REL)
                    bs.seek(bs.readInt() - 4, NOESEEK_REL)  # --> number of parts
                    parts = bs.readInt()
                    bs.seek(bs.readInt() - 4, NOESEEK_REL)  # --> materials
                    partMaterials = []
                    for p in range(0, parts):
                        partMaterials.append(bs.readInt())
                    partMaterials = list(reversed(partMaterials))
                    bs.seek(stack.pop(), NOESEEK_ABS)
                    bonePartPair = BonePartPair(2, j, parts, partMaterials)
                    layer.bonePartPairs.append(bonePartPair)

        if (layer.p4 != 0):
            bs.seek(layer.p4, NOESEEK_ABS)
            bs.seek(8, NOESEEK_REL)
            bs.seek(bs.readInt() - 4, NOESEEK_REL)  # --> matrix
            bs.seek(0xB0, NOESEEK_REL)
            bs.seek(bs.readInt() - 4, NOESEEK_REL)  # --> number of parts
            parts = bs.readInt()
            bs.seek(bs.readInt() - 4, NOESEEK_REL)  # --> materials
            partMaterials = []
            for p in range(0, parts):
                partMaterials.append(bs.readInt())
            partMaterials = list(reversed(partMaterials))
            # bs.seek(stack.pop(), NOESEEK_ABS)
            bonePartPair = BonePartPair(3, -1, parts, partMaterials)
            layer.bonePartPairs.append(bonePartPair)

    bs.seek(abs_offset_bones, NOESEEK_ABS)
    bones = []
    bones1 = []
    boneNames = []
    bonePIndices = []
    for i in range(0, number_bones):
        bs.readBytes(0x40)
        bs.seek(0xc, NOESEEK_REL)
        offsetText = bs.readInt()
        stack.append(bs.tell())
        bs.seek(offsetText - 4, NOESEEK_REL)
        boneName = bs.readString()
        boneNames.append(boneName)
        bs.seek(stack.pop(), NOESEEK_ABS)
        bonePIndex = bs.readByte()
        bonePIndices.append(bonePIndex)
        bs.readByte()
        bs.readByte()
        bs.readByte()
        bs.readInt()
        bs.readInt()
        bs.readInt()
        print(boneName + ": " + repr(i) + "-->" + repr(bonePIndex))

    for i in range(0, number_bones):
        boneMat = NoeMat44.fromBytes(bs.readBytes(0x40)).toMat43()
        # print(boneMat)
        if (bonePIndices[i] != -1):
            boneMat = boneMat.__mul__(bones1[bonePIndices[i]])
        bone = NoeBone(i, boneNames[i], boneMat, None, bonePIndices[i])
        bones.append(bone)
        bones1.append(boneMat)

    for i in range(0, number_bones):
        boneMat = NoeMat44.fromBytes(bs.readBytes(0x40)).toMat43()

    globalCounter = 0
    for layer in (layers):
        print("Layer: %d" % layer.layer)
        if layer.bonePartPairs:
            for bonePartPair in (layer.bonePartPairs):
                print("  Pointer: " + repr(bonePartPair.pointer) + " Bone: " + repr(
                    bonePartPair.bone) + " Parts: " + repr(bonePartPair.parts))
                if (bonePartPair.bone != -1):
                    rapi.rpgSetTransform(bones1[bonePartPair.bone])
                else:
                    rapi.rpgSetTransform(None)
                print(bonePartPair.partMaterials)
                for j in range(0, bonePartPair.parts):
                    rapi.rpgBindPositionBuffer(bytesForPositions[globalCounter], noesis.RPGEODATA_FLOAT,
                                               stride[globalCounter], 0)
                    if (stride[globalCounter] == 44):
                        rapi.rpgBindUV1BufferOfs(bytesForPositions[globalCounter], noesis.RPGEODATA_FLOAT,
                                                 stride[globalCounter], 28)
                        # rapi.rpgBindBoneIndexBufferOfs(bytesForPositions[globalCounter], noesis.RPGEODATA_UBYTE, stride[globalCounter], 40, 4)
                        # rapi.rpgBindBoneWeightBufferOfs(bytesForPositions[globalCounter], noesis.RPGEODATA_UBYTE, stride[globalCounter], 36, 4)
                    if (stride[globalCounter] == 40):
                        rapi.rpgBindUV1BufferOfs(bytesForPositions[globalCounter], noesis.RPGEODATA_FLOAT,
                                                 stride[globalCounter], 24)
                        # rapi.rpgBindBoneIndexBufferOfs(bytesForPositions[globalCounter], noesis.RPGEODATA_UBYTE, stride[globalCounter], 36, 4)
                        # rapi.rpgBindBoneWeightBufferOfs(bytesForPositions[globalCounter], noesis.RPGEODATA_UBYTE, stride[globalCounter], 32, 4)
                    if (stride[globalCounter] == 36):
                        if NU20 == 0x3032554e:  # Batman
                            rapi.rpgBindUV1BufferOfs(bytesForPositions[globalCounter], noesis.RPGEODATA_FLOAT,
                                                     stride[globalCounter], 20)
                        else:
                            rapi.rpgBindUV1BufferOfs(bytesForPositions[globalCounter], noesis.RPGEODATA_FLOAT,
                                                     stride[globalCounter], 28)
                    if (stride[globalCounter] == 32):
                        rapi.rpgBindUV1BufferOfs(bytesForPositions[globalCounter], noesis.RPGEODATA_FLOAT,
                                                 stride[globalCounter], 24)
                    if (stride[globalCounter] == 28):
                        if NU20 == 0x3032554e:  # Batman
                            rapi.rpgBindUV1BufferOfs(bytesForPositions[globalCounter], noesis.RPGEODATA_FLOAT,
                                                     stride[globalCounter], 20)
                    rapi.rpgSetMaterial("mat%03i" % bonePartPair.partMaterials[j])
                    rapi.rpgCommitTriangles(bytesForIndexBuffer[globalCounter], noesis.RPGEODATA_SHORT,
                                            numIdx[globalCounter], noesis.RPGEO_TRIANGLE_STRIP, 1)
                    globalCounter = globalCounter + 1
                    rapi.rpgClearBufferBinds()

            mdl = rapi.rpgConstructModel()
            mdl.setModelMaterials(NoeModelMaterials(textures, materials))
            mdl.setBones(bones)
            mdlList.append(mdl)  # important, don't forget to put your loaded model in the mdlList

    return 1


class Layer(object):
    def __init__(self, layer):
        self.layer = layer
        self.bonePartPairs = []
        self.p1 = 0
        self.p2 = 0
        self.p3 = 0
        self.p4 = 0


class BonePartPair(object):
    def __init__(self, pointer, bone, parts, partMaterials):
        self.pointer = pointer
        self.bone = bone
        self.parts = parts
        self.partMaterials = partMaterials


class ImageMeta(object):
    def __init__(self, width, height, size):
        self.width = width
        self.height = height
        self.size = size
