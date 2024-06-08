# import numpy
import json
import os
import weight
import json_stringify

FRAME_T = 30  # spine設定 30幀為1秒
folder_path = ""
file_name = ""

jsonFile = open("json/wfx_Symbol.json", "r")
jData = json.load(jsonFile)

animationList = {}  # ["animation_name"] = Animation

"""
架構
animationList (Dictionary) : 存各個 Aniamtion
    Animation (class) : 存 動畫名稱 和 AniBone
        AniBone (class) : 存 動畫作用的骨架名稱 和 3種Data的List
            Scale/Rotate/TransData (class) : 存 keyframe的time value curve

"""


class AniBone:  # bone底下有哪些動畫曲線
    def __init__(self, name, rList=[], sList=[], tList=[]):
        self.name = name
        self.rotateList = rList  # list of ScaleData
        self.scaleList = sList  # list of RotateData
        self.transList = tList  # list of TransData


class Animation:
    def __init__(self, aniName):
        self.name = aniName  # animation's name
        self.aniBoneList = []  # [] = AniBone

    def AddAniBone(self, aniBone):
        self.aniBoneList.append(aniBone)


class ScaleData:
    def __init__(self, time, x, y, cList=[], isStepped=False):
        self.time = float(time)  # 單位:sec
        self.x = float(x)
        self.y = float(y)
        if isStepped:
            self.curve = "stepped"
        else:
            self.curve = self.SetCurve(cList)  # frame之間的曲線控制點
        # empty list 代表不需要curve
        # scale曲線分x,y，都存在同個list裡
        # x: cx1,cy1,cx2,cy2 ; y: cx1,cy1,cx2,cy2

    def SetCurve(self, cList):
        if len(cList) != 0 and len(cList) < 8:
            print(f"Scale curve list error. frame:{self.time}")
            return []
        return cList

    # def Time(self):  # 單位:sec
    #     return round(self.time / FRAME_T, 4)


# 改成第幾幀直接存自己的curve值, 不要取下一幀(下一幀不一定是用curve)
class RotateData:

    def __init__(self, time, value, cList=[], isStepped=False):
        self.time = float(time)  # 單位:sec
        self.value = float(value)
        if isStepped:
            self.curve = "stepped"
        else:
            self.curve = self.SetCurve(cList)  # frame之間的曲線控制點

    def SetCurve(self, cList):
        if len(cList) != 0 and len(cList) < 4:
            print(f"Rotate curve list error at frame time = {self.time}")
            return []
        return cList

    # def Time(self):  # return 單位:sec
    #     return round(self.time / FRAME_T, 4)


class TransData:
    def __init__(self, time, x, y, cList=[], isStepped=False):
        self.time = float(time)  # 單位:sec
        self.x = float(x)
        self.y = float(y)
        if isStepped:
            self.curve = "stepped"
        else:
            self.curve = self.SetCurve(cList)  # frame之間的曲線控制點

    def SetCurve(self, cList):
        if len(cList) != 0 and len(cList) < 8:
            print(f"Translate curve list error. frame:{self.time}")
            return []
        return cList


def SetImgPath(img_path):
    global folder_path, file_name
    folder_path, file_name = os.path.split(img_path)


def Parse():
    # for i in jDict:
    #     print(i, jDict[i]) # animation's name, {values}
    for mainKey, mainValue in jData.items():
        if mainKey == "animations":
            for aKey, aValue in mainValue.items():
                ParseAnimations(aKey, aValue)


def ParseAnimations(aniName, animation):
    newAnimation = Animation(aniName)
    animationList[newAnimation.name] = newAnimation
    if len(animation) == 0:
        print("No animation descriptions.\n")
        return
    for mainKey, mainValue in animation.items():  # animation作用在哪類物件上

        match mainKey:
            case "bones":  # 哪個 bone 的 animation
                for bKey, bValue in mainValue.items():
                    ParseCurve(bKey, bValue, newAnimation)
            case _:  # default
                continue


def ParseCurve(boneName, animation, newAnimation):
    newAniBone = AniBone(boneName)
    newAnimation.AddAniBone(newAniBone)
    animationList[newAnimation.name] = newAnimation  # refresh Animation
    for mainKey, mainValue in animation.items():
        match mainKey:
            case "scale":
                ParseScale(mainValue, newAnimation)  # Scale (list of obj)
            case "rotate":
                ParseRotate(mainValue, newAnimation)  # Rotate (list of obj)
            case "translate":
                ParseTranslate(mainValue, newAnimation)  # Translate (list of obj)
            case _:  # default
                continue


def ParseScale(sList, newAnimation):
    scaleList = []  # 每幀的縮放資訊(ScaleData)
    for frameObj in sList:
        time = 0.0
        x = 1.0
        y = 1.0
        isStepped = False
        cList = []
        for fKey, fValue in frameObj.items():
            match fKey:
                case "time":
                    time = fValue
                case "x":
                    x = fValue
                case "y":
                    y = fValue
                case "curve":  # curve 有 bezier 或 stepped 兩種
                    if isinstance(fValue, str):
                        if fValue == "stepped":
                            isStepped = True
                    elif isinstance(fValue, list):
                        cList = fValue
                case _:  # default
                    continue

        s = ScaleData(time, x, y, cList, isStepped)
        scaleList.append(s)

    # refresh last(current) AinBone (r,s,t)
    newAnimation.aniBoneList[-1].scaleList = scaleList
    animationList[newAnimation.name] = newAnimation  # refresh Animation
    # for data in scaleList:
    #     print(data.time, data.x, data.y, data.curve)


def ParseRotate(rList, newAnimation):
    rotateList = []  # 每幀的旋轉資訊(RotateData)
    for frameObj in rList:
        time = 0.0
        value = 0.0
        cList = []
        isStepped = False
        for fKey, fValue in frameObj.items():

            match fKey:
                case "time":
                    time = fValue
                case "value":
                    value = fValue
                case "curve":  # curve 有 bezier 或 stepped 兩種
                    if isinstance(fValue, str):
                        if fValue == "stepped":
                            isStepped = True
                    elif isinstance(fValue, list):
                        cList = fValue
                case _:  # default
                    continue

        r = RotateData(time, value, cList, isStepped)
        rotateList.append(r)

    # refresh last(current) AinBone (r,s,t)
    newAnimation.aniBoneList[-1].rotateList = rotateList
    animationList[newAnimation.name] = newAnimation  # refresh Animation
    # for data in rotateList:
    #     print(data.time, data.value, data.curve)


def ParseTranslate(tList, newAnimation):
    transList = []  # 每幀的縮放資訊(ScaleData)
    for frameObj in tList:
        time = 0.0
        x = 0.0
        y = 0.0
        cList = []
        isStepped = False
        for fKey, fValue in frameObj.items():
            match fKey:
                case "time":
                    time = fValue
                case "x":
                    x = fValue
                case "y":
                    y = fValue
                case "curve":  # curve 有 bezier 或 stepped 兩種
                    if isinstance(fValue, str):
                        if fValue == "stepped":
                            isStepped = True
                    elif isinstance(fValue, list):
                        cList = fValue
                case _:  # default
                    continue

        s = TransData(time, x, y, cList, isStepped)
        transList.append(s)

    # refresh last(current) AinBone's list
    newAnimation.aniBoneList[-1].transList = transList
    animationList[newAnimation.name] = newAnimation  # refresh Animation
    # for data in transList:
    #     print(data.time, data.x, data.y, data.curve)


def main():

    Parse()
    # for key, ani in animationList.items():
    #     print("animation: " + ani.name)
    #     for ani_bone in ani.aniBoneList:
    #         print("bone: " + ani_bone.name)
    #         print("\n\tscale:")
    #         for index, data in enumerate(ani_bone.scaleList):
    #             print("{")
    #             print(f'"time": {data.time},')
    #             print(f'"x": {data.x},')
    #             print(f'"y": {data.y},')
    #             print(f'"curve": {data.curve}')
    #             if index == len(ani_bone.scaleList) - 1:
    #                 print("}")
    #             else:
    #                 print("},")

    #         print("\n\trotate:")
    #         for index, data in enumerate(ani_bone.rotateList):
    #             print("{")
    #             print(f'"time": {data.time},')
    #             print(f'"value": {data.value},')
    #             print(f'"curve": {data.curve}')
    #             if index == len(ani_bone.rotateList) - 1:
    #                 print("}")
    #             else:
    #                 print("},")

    #         print("\n\ttranslate:")
    #         for index, data in enumerate(ani_bone.transList):
    #             print("{")
    #             print(f'"time": {data.time},')
    #             print(f'"x": {data.x},')
    #             print(f'"y": {data.y},')
    #             print(f'"curve": {data.curve}')
    #             if index == len(ani_bone.transList) - 1:
    #                 print("}")
    #             else:
    #                 print("},")
    #         print("\n")

    ## curve的x要再轉成整體時長的"比例"(現在單位是秒)
    json_stringify.OutputJson(animationList, folder_path, file_name)


if __name__ == "__main__":
    main()


# 貝茲曲線的控制點怎麼計算?
# 計算左右控制點和幀座標點之間的斜率(左右斜率一致)
#   用這幀和下幀算斜率(最後一幀延續前一幀算的斜率)，
#   把斜率(根據旋轉效果強弱把斜率縮小或增加一點)套到這幀的貝茲的左右控制點上，
#   X值取這幀和下幀的中間秒數(算出秒再/總時長轉成cx)，再套斜率求出Y值
