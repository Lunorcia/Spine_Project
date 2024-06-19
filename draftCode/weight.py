import numpy


class Bone:
    def __init__(self, name, parent="", x=0.0, y=0.0, scaleY=1.0, isF=False):
        self.name = name
        self.parent = parent
        self.x = x
        self.y = y
        self.scaleY = scaleY
        self.transform = "normal"
        if isF:
            self.transform = "onlyTranslation"


class Vertex:
    def __init__(self, FS, FR, F, x=0.0, y=0.0, index=0, weightIndex=0):
        self.x = x
        self.y = y
        self.FS = FS  # Bone    # FS.x=0(軸心), FS.y = vertex.y, scaleY = 0.01
        self.FR = FR  # Bone
        self.F = F  # Bone      # F.x = vertex.x, y跟著FS(json預設)
        self.index = index  # 求weightIndex時當索引值用 (順時針由內往外遞增)
        self.weightIndex = weightIndex  # 權重綁定的順序，依照 x 小到大排序(最右邊的點層級最高, index最大)


# 建立vertex骨架層級
def CreateBones(vertexList, outerNum):
    # # list outer和inner對調
    # vertexList = vertexList[outerNum:] + vertexList[:outerNum] # [num~last]是inner， [從0開始取num個]是outer
    # # inner + outer
    # for i, vertex in enumerate(vertexList):
    #     0

    # current vertex list : outer + inner (逆時針)
    vertexList = numpy.squeeze(vertexList)
    # reverse list : inner + outer (順時針)
    cwvList = vertexList[::-1]
    vList = []  # Vertex(class) list (順時針)
    for i, vertex in enumerate(cwvList):
        fs = Bone("FS" + str(i), "Front", 0, vertex[1], 0.01, False)  # FS.y = vertex.y
        fr = Bone("FR" + str(i), fs.name, 0, vertex[1], 1, False)
        f = Bone("F" + str(i), fr.name, vertex[0], vertex[1], 0, True)  # F.x = vertex.x
        # print(f"fs:{fs.name,fs.parent,fs.x,fs.y,fs.scaleY,fs.transform}\n")
        # print(f"fr:{fr.name,fr.parent, fr.x,fr.y,fr.scaleY,fr.transform}\n")
        # print(f"f:{f.name,f.parent,f.x,f.y,f.scaleY,f.transform}\n")
        v = Vertex(fs, fr, f, vertex[0], vertex[1], i, 0)

        vList.append(v)

    sorted_indices = sorted(
        vList, key=lambda vertex: vertex.x
    )  # vertices 按 x 由小到大排序，取得weightIndex

    for i, vertex in enumerate(sorted_indices):
        vList[vertex.index].weightIndex = i  # vertex.index=未排序前的(vList)index

    # 把list index倒轉回去，存回json要用逆時針
    vList = vList[::-1]
    return vList


def PrintBones(vList):
    path = "bones.txt"
    f = open(path, "w")
    for vertex in vList:
        # FS
        f.write("{\n")
        lines = ['"name": "', vertex.FS.name, '",\n']
        f.writelines(lines)
        lines = ['"parent": "', vertex.FS.parent, '",\n']
        f.writelines(lines)
        lines = ['"y":', str(vertex.FS.y), ",\n"]
        f.writelines(lines)
        lines = ['"scaleY":', str(vertex.FS.scaleY), "\n"]
        f.writelines(lines)
        f.write("},\n")
        # FR
        f.write("{\n")
        lines = ['"name": "', vertex.FR.name, '",\n']
        f.writelines(lines)
        lines = ['"parent": "', vertex.FR.parent, '"\n']
        f.writelines(lines)
        f.write("},\n")
        # F
        f.write("{\n")
        lines = ['"name": "', vertex.F.name, '",\n']
        f.writelines(lines)
        lines = ['"parent": "', vertex.F.parent, '",\n']
        f.writelines(lines)
        lines = ['"x":', str(vertex.F.x), ",\n"]
        f.writelines(lines)
        lines = ['"transform": "', vertex.F.transform, '"\n']
        f.writelines(lines)
        f.write("},\n")

    f.close()


# 根據 weightIndex 為 Vertex 的 "F" 在json綁定權重 = 1
def PrintVertexWeight(vList):
    path = "vertices.txt"
    f = open(path, "w")
    for vertex in vList:
        lines = [
            "1, ",
            str(vertex.weightIndex),
            ", ",
            "0",    # str(vertex.x),
            ", ",
            "0",    # str(vertex.y),
            ",\n",
            ", 1,\n",
        ]
        f.writelines(lines)
        # print(f"1, {vertex.weightIndex}, {vertex.x}, {vertex.y}, 1", end=",\n")

    f.close()


"""
每個vertex建一個骨骼層級 : FSn (軸心) -> FRn (旋轉) -> Fn (控制位移, 不繼承旋轉&縮放)
不動可以不寫在json (自動用默認值)

FS.x 不動(0) (圖片旋轉中心), FS.y = vertex.y, scaleY = 0.01 (不改要預設1)
FR 跟FS同位置(0,FS.y)
F.x = vertex.x, f.y 不動(繼承FS.y)

從內輪廓開始 順時針(現在vertices是逆時針,要倒著建) 建骨骼，內建完再換外(一樣要用順時針)
綁權重前先把 vertices 建新排序 
按照 vertices 排序 F (把index寫進class裡)
>>>>>>> vertices 按 x 由小到大排序, index = 0 ~ n-1 (最右邊的點層級最高, index最大)  ###done

~(不需要)找 F.x && FS.y == vertex.x,y 的~
根據 weightIndex 為 Vertex 自己的"F" 在json綁定權重=1
json格式: {# of bones(=1), boneIndex, vertex.x, vertex.y, weight=1}
"""
