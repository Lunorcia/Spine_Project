import cv2
import numpy
import triangle
import weight

image_file = "../static/Image/Qe.png"
scale = 10  # 縮放比例 (原始圖片太小時需放大)
outer_ep = 0.003  # 調整輪廓近似精細度的參數 (ep越小輪廓越精細，輪廓點也越多)
inner_ep = 0.005
gray = 0  # 測試用才搬出來的

need_inner = True  # 需不需要找內輪廓 (ex: Q, A)

def SetImgPath(img_path):
    image_file = img_path

def PreprocessImage(img, scale, width, height):

    img = cv2.resize(img, ((width * scale), (height * scale)))  # 放大image以取得輪廓

    blur = cv2.medianBlur(img, 9)  # 模糊化，去除雜訊
    gray = cv2.cvtColor(
        blur, cv2.COLOR_RGBA2GRAY
    )  # 轉成灰階 COLOR_RGBA2GRAY COLOR_BGR2GRAY
    gray = cv2.GaussianBlur(gray, (15, 15), 0)

    ret, binary = cv2.threshold(
        gray, 230, 255, cv2.THRESH_BINARY
    )  # 二值化 大於門檻值的灰階值設為最大灰階值255(白)，小於門檻值的值設為0(黑)。  ## threshold門檻值有問題

    ## for showing test
    # cv2.namedWindow("img", cv2.WINDOW_NORMAL)
    # cv2.resizeWindow("img", 200, 200)
    # cv2.imshow("img", binary)
    # cv2.waitKey()
    binary = cv2.Canny(binary, 40, 180)

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT, (5, 5)
    )  # 設定kernel滾動作用的像素範圍
    dilated = cv2.dilate(binary, kernel)  # 膨脹操作
    eroded = cv2.erode(dilated, kernel)  # 腐蝕操作

    img_resized = img.copy()

    return img, img_resized, eroded  # 用來找輪廓的image


def GetApproxContour(eroded, img, img_resized):

    contours, hierarchy = cv2.findContours(
        eroded, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE
    )  # RETR_EXTERNAL 只找最外圍輪廓  #RETR_TREE 樹狀結構

    cv2.drawContours(img, contours[0], -1, (0, 0, 255), 3)
    print("contour node # = " + str(len(contours[0])))

    # 找內輪廓近似
    approx_inner = None
    if need_inner:
        approx_inner = GetInnerApproxContour(contours, img_resized)

    # 外輪廓近似
    epsilon = outer_ep * cv2.arcLength(contours[0], True)
    approx_outer = cv2.approxPolyDP(contours[0], epsilon, True)
    # 畫輪廓點位置
    approx_img = cv2.drawContours(img_resized, [approx_outer], -1, (255, 0, 0), 2)
    for i in range(len(approx_outer)):
        # print(str(i) + ' : '+ str(approx[i][0][0]) + ',' + str(approx[i][0][1]))
        cv2.circle(
            img_resized,
            (approx_outer[i][0][0], approx_outer[i][0][1]),
            3,
            (0, 255, 0),
            1,
        )
        cv2.putText(
            img_resized,
            str(i),
            (approx_outer[i][0][0], approx_outer[i][0][1]),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 0, 255),
            3,
        )
    print("approx node # = " + str(len(approx_outer)))

    cv2.namedWindow("img", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("img", 200, 200)
    cv2.imshow("img", img)  # 未做近似的原始輪廓

    cv2.namedWindow("approx", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("approx", 200, 200)
    cv2.imshow("approx", approx_img)  # 近似後的輪廓

    # cont0_area = cv2.contourArea(contours[0])
    # print('cont0 面積=' + str(cont0_area))
    # approx_area = cv2.contourArea(approx)
    # print('approx 面積=' + str(approx_area))

    # for index, appr in enumerate(approx):
    #     print('第{}個頂點的位置：{}'.format(index, appr))

    return approx_outer, approx_inner  # 輪廓的vertice


def GetInnerApproxContour(contours, img_resized):

    # 排序輪廓大小(有內輪廓時使用)
    areas = []
    for cont in contours:
        areas.append(cv2.contourArea(cont))
    areas = numpy.array(areas)
    index = areas.argsort()

    # 找到圖片整體(中間空洞填滿)的mask
    # mask = numpy.zeros_like(gray, dtype = numpy.uint8)
    # mask = cv2.drawContours(mask, contours, index[-2], (255, 255, 255), thickness = -1) #index照面積大小排序了 -2整體, -4內中空範圍
    # cv2.namedWindow("inner", cv2.WINDOW_NORMAL)
    # cv2.resizeWindow("inner", 200, 200)

    # for i in range(len(index)):
    # inner = img.copy()
    # inner = cv2.drawContours(inner, contours, index[i], (0, 255, 0), 2) #index照面積由小到大排序了， i= -2整體, -4內中空範圍
    # inner_area = cv2.contourArea(contours[i])
    # print(f'inner {i} 面積=' + str(inner_area))
    # cv2.imshow("inner", inner)  # 內部輪廓
    # cv2.waitKey(0)

    # 選擇面積最大的輪廓
    # max_contour = max(contours, key = cv2.contourArea)
    # 繪製輪廓
    # cv2.drawContours(img, [max_contour], -1, (0, 0, 255), 3)

    # 輪廓近似
    epsilon = inner_ep * cv2.arcLength(
        contours[index[-3]], True
    )  # -3內輪廓中空範圍(逆時針)
    approx_inner = cv2.approxPolyDP(contours[index[-3]], epsilon, True)
    # 畫輪廓點位置
    approx_img = cv2.drawContours(img_resized, [approx_inner], -1, (255, 255, 0), 2)
    for i in range(len(approx_inner)):
        # print(str(i) + ' : '+ str(approx[i][0][0]) + ',' + str(approx[i][0][1]))
        cv2.circle(
            img_resized,
            (approx_inner[i][0][0], approx_inner[i][0][1]),
            3,
            (0, 255, 0),
            1,
        )
        cv2.putText(
            img_resized,
            str(i),
            (approx_inner[i][0][0], approx_inner[i][0][1]),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 0, 255),
            3,
        )

    print("inner approx node # = " + str(len(approx_inner)))
    # cv2.namedWindow("inner approx", cv2.WINDOW_NORMAL)
    # cv2.resizeWindow("inner approx", 200, 200)
    # cv2.imshow("inner approx", approx_img)    # 近似後的輪廓

    return approx_inner


# 座標轉換為在原大小image的位置，在原大小image繪製輪廓
def ReScaleVertices(approx_cp, scale, origin_img):

    for point in approx_cp:
        point[0][0] = int(point[0][0] / scale)
        point[0][1] = int(point[0][1] / scale)

    # cv2.drawContours(origin_img, [approx_cp], -1, (0, 0, 255), 1)  # 畫輪廓線
    # 標示座標點位置
    for i in range(len(approx_cp)):
        # print(str(i) + ' origin: '+ str(approx_cp[i][0][0]) + ',' + str(approx_cp[i][0][1]))
        cv2.circle(
            origin_img, (approx_cp[i][0][0], approx_cp[i][0][1]), 1, (0, 255, 0), -1
        )
        cv2.putText(
            origin_img,
            str(i),
            (approx_cp[i][0][0], approx_cp[i][0][1]),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.2,
            (255, 0, 255),
            1,
        )  # 標示座標點index

    cv2.namedWindow("origin", cv2.WINDOW_NORMAL)  # 近似後的原始圖像的輪廓
    cv2.resizeWindow("origin", 200, 200)
    cv2.imshow("origin", origin_img)

    return approx_cp, origin_img


# # 三角剖分
# def GetMesh(approx_cp, origin_img):

#     rect = cv2.boundingRect(approx_cp)
#     subdiv = cv2.Subdiv2D(rect)
#     for point in approx_cp:
#         subdiv.insert((int(point[0][0]), int(point[0][1])))  # 座標點傳入subdiv

#     triangle_list = subdiv.getTriangleList()
#     approx_list = numpy.squeeze(approx_cp)
#     canvas = numpy.zeros_like(origin_img)  # 畫三角剖分用的image
#     cv2.namedWindow("Canvas", cv2.WINDOW_NORMAL)  # 三角剖分結果
#     cv2.resizeWindow("Canvas", 200, 200)
#     # draw triangle
#     for triangle in triangle_list:  # x1,y1; x2,y2; x3,y3
#         pt1 = [int(triangle[0]), int(triangle[1])]
#         pt2 = [int(triangle[2]), int(triangle[3])]
#         pt3 = [int(triangle[4]), int(triangle[5])]
#         index_pt1 = -1
#         index_pt2 = -1
#         index_pt3 = -1
#         # 找三角形頂點在輪廓中的index
#         for i in range(len(approx_list)):
#             if approx_list[i][0] == pt1[0] and approx_list[i][1] == pt1[1]:
#                 index_pt1 = i
#                 continue
#             if approx_list[i][0] == pt2[0] and approx_list[i][1] == pt2[1]:
#                 index_pt2 = i
#                 continue
#             if approx_list[i][0] == pt3[0] and approx_list[i][1] == pt3[1]:
#                 index_pt3 = i
#                 continue
#         print(f"{index_pt1}, {index_pt2}, {index_pt3},")  # 三角頂點index
#         cv2.line(canvas, pt1, pt2, (0, 255, 0), 1)
#         cv2.line(canvas, pt2, pt3, (0, 255, 0), 1)
#         cv2.line(canvas, pt3, pt1, (0, 255, 0), 1)
#         cv2.imshow("Canvas", canvas)
#         # cv2.waitKey(0)


# new func to get mesh
def TriangleMesh(approx_cp, outer_num, origin_img):

    approx_list = numpy.squeeze(approx_cp)  # get vertices
    # edge_vertices = approx_list[:outer_num]  # get outer vertex (to create edge)
    segments = []  # 輪廓要繪製mesh的範圍(edges)
    for i in range(outer_num):  # 0~n-1
        if i == (outer_num - 1):  # 最後一條edge連回0
            edge = [i, 0]
            segments.append(edge)
        else:
            edge = [i, i + 1]
            segments.append(edge)

    t = triangle.triangulate({"vertices": approx_list, "segments": segments}, "p")
    t_list = t["triangles"].tolist()
    # ts = t["segments"].tolist()
    # print(f"t.segments: {ts}\n")
    # print(f"triangle list: {t_list}\n")

    path = "triangles.txt"
    f = open(path, "w")
    for tri in t_list:
        lines = [str(tri[0]), ", ", str(tri[1]), ", ", str(tri[2]), ",\n"]
        f.writelines(lines)
    f.close()

    canvas = numpy.zeros_like(origin_img)  # 畫三角剖分用的image
    cv2.namedWindow("Canvas", cv2.WINDOW_NORMAL)  # 三角剖分結果
    cv2.resizeWindow("Canvas", 200, 200)
    # draw triangle
    for tri in t_list:  # x1,y1; x2,y2; x3,y3
        index_pt1 = tri[0]
        index_pt2 = tri[1]
        index_pt3 = tri[2]
        pt1 = approx_list[index_pt1]
        pt2 = approx_list[index_pt2]
        pt3 = approx_list[index_pt3]

        cv2.line(canvas, pt1, pt2, (0, 255, 0), 1)
        cv2.line(canvas, pt2, pt3, (0, 255, 0), 1)
        cv2.line(canvas, pt3, pt1, (0, 255, 0), 1)
        cv2.imshow("Canvas", canvas)
        # cv2.waitKey(0)


# vertex座標轉換成Spine的world transfrom((0,0)為圖片中心)
def GetVerticeCoordinate(approx_cp, width, height):

    approx_final = approx_cp.copy()
    approx_final = approx_final.astype(float)  # 轉成float表示座標
    for point in approx_final:
        point[0][1] *= -1  # 原輪廓座標為左上角(0, 0)往下Y值為正 -> Y值翻轉(往下為負)
        point[0][0] -= width / 2  # 座標點往左上平移
        point[0][1] += height / 2

    # print("vertex coordinate : ")
    # for point in approx_final:
    #     print(f"{point[0][0]}, {point[0][1]},", end="\n")

    return approx_final  # 轉換後的vertice座標


# 計算uv座標(圖片左上(0, 0)，右下(1, 1))
def GetUVCoordinate(approx_final, width, height):

    uv = approx_final.copy()
    uL = width * (-1) / 2  # vertex左上座標
    vT = height / 2
    for point in uv:
        point[0][0] = round((point[0][0] - uL) / width, 6)
        point[0][1] = round(abs(point[0][1] - vT) / height, 6)

    path = "uvs.txt"
    f = open(path, "w")
    for point in uv:
        lines = [str(point[0][0]), ", ", str(point[0][1]), ",\n"]
        f.writelines(lines)
        # print(f"{point[0][0]}, {point[0][1]},", end="\n")
    f.close()
    return uv


def main():

    img = cv2.imread(image_file)
    origin_img = img.copy()  # 原image大小
    height, width = img.shape[:2]

    img, img_resized, eroded = PreprocessImage(img, scale, width, height)
    approx_outer, approx_inner = GetApproxContour(eroded, img, img_resized)
    approx_cp = approx_outer.copy()
    outer_num = len(approx_outer)  # 外輪廓有幾個頂點
    if need_inner:
        # approx_cp = approx_inner.copy()
        approx_cp = numpy.concatenate(
            (approx_cp, approx_inner), axis=0
        )  # 把inner接在outer後面

    approx_cp, origin_img = ReScaleVertices(
        approx_cp, scale, origin_img
    )  # 轉換vertices座標，在原大小image繪製輪廓

    # GetMesh(approx_cp, origin_img)  # origin_img用來建空畫布
    TriangleMesh(approx_cp, outer_num, origin_img)

    approx_final = GetVerticeCoordinate(approx_cp, width, height)
    uv = GetUVCoordinate(approx_final, width, height)

    # 需要幾條邊

    print(f"outer_num (hull) = {outer_num}")
    for i in range(outer_num):  # 0~n-1
        if i == (outer_num - 1):  # 最後一條edge連回0
            print(f"{i * 2}, 0")
        else:
            print(f"{i * 2}, {(i + 1) * 2},", end=" ")

    vList = weight.CreateBones(approx_final, outer_num)  # 建立骨架層級
    # for vertex in vList:
    #     print(
    #         f"vertex index:{vertex.index}, weightIndex:{vertex.weightIndex}\tFS:{vertex.FS.name, vertex.FS.x, vertex.FS.y}\tFR:{vertex.FR.name, vertex.FR.x, vertex.FR.y}\tF:{vertex.F.name, vertex.F.x, vertex.F.y}\n"
    #     )

    weight.PrintVertexWeight(vList)
    weight.PrintBones(vList)

    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
