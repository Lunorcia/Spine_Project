import cv2
import json
import hashlib
import base64
import random
import string
import os
import pathlib

SRC_PATH = pathlib.Path(
    __file__
).parent.parent.absolute()  # (json_.py)'s grandparent path = /HTML
# src = -absolute path-\HTML
# location of json file which program saved
JSON_FILE_FOLDER = os.path.join(SRC_PATH, "static", "JsonFile")


def GenerateHash(value, length=11):
    hash_obj = hashlib.sha256()
    hash_obj.update(value.encode("utf-8"))
    binary_hash = hash_obj.digest()
    base64_hash = base64.urlsafe_b64encode(binary_hash).decode("utf-8")
    return base64_hash[:length]


def GenerateRandomStr(length=11):
    characters = string.ascii_letters + string.digits
    random_string = "".join(random.choice(characters) for _ in range(length))
    return random_string


def SkeletonInfo(folder_path):

    hash_value = GenerateHash(GenerateRandomStr())
    skeleton = {
        "hash": hash_value,
        "spine": "4.2.20",
        "images": f"{folder_path}",
        "audio": "",
    }
    return skeleton


def BonesInfo():

    bones = [
        {"name": "root"},
        {"name": "All", "parent": "root"},
        {"name": "MainSYM", "parent": "All"},
        {"name": "Down", "parent": "MainSYM", "y": -71.39},
        {"name": "Middle", "parent": "Down", "y": 71.39},
        {"name": "M1", "parent": "Middle"},
    ]
    return bones


def SlotsInfo(file_name):

    slots = [{"name": "sym", "bone": "M1", "attachment": f"{file_name}"}]
    return slots


def SkinsInfo(folder_path, file_name):

    file_path = os.path.join(folder_path, file_name)
    img = cv2.imread(file_path)
    height, width = img.shape[:2]
    skins = [
        {
            "name": "default",
            "attachments": {
                "sym": {f"{file_name}": {"width": width, "height": height}}
            },
        }
    ]
    return skins


def AnimationInfo(animationList):
    """
    "ani Name":
    {
        "bones":
        {
            "boneName1":{
                        "scale curve":[0.0,1.1,...],
                        "rotate curve":[...],
                        "translate curve":[...]
                    },
            "boneName2":{...}
        }
    }
    """
    anis_dict = {}
    for key, ani in animationList.items():
        # print("animation: " + ani.name)
        bones_dict = {}
        for ani_bone in ani.aniBoneList:
            # print("bone: " + ani_bone.name)
            scale_curve = []
            rotate_curve = []
            trans_curve = []
            for index, data in enumerate(ani_bone.scaleList):
                frame = {
                    "time": data.time,
                    "x": data.x,
                    "y": data.y,
                    "curve": data.curve,
                }
                scale_curve.append(frame)

            for index, data in enumerate(ani_bone.rotateList):
                frame = {"time": data.time, "value": data.value, "curve": data.curve}
                rotate_curve.append(frame)

            for index, data in enumerate(ani_bone.transList):
                frame = {
                    "time": data.time,
                    "x": data.x,
                    "y": data.y,
                    "curve": data.curve,
                }
                trans_curve.append(frame)

            bone_curves = {
                "scale": scale_curve,
                "rotate": rotate_curve,
                "translate": trans_curve,
            }
            bones_dict.update({f"{ani_bone.name}": bone_curves})
        # 目前animation需要的只有作用在bones上的動畫資訊
        bb_dict = {"bones": bones_dict}
        anis_dict.update({f"{ani.name}": bb_dict})
    return anis_dict
    # print(anis_dict)
    # with open("ani.json", "w") as j:  # create json file
    #     json.dump(anis_dict, j)


"""
animationList = {}  # ["animation_name"] = Animation
架構
animationList (Dictionary) : 存各個 Aniamtion
    Animation (class) : 存 動畫名稱 和 AniBone
        AniBone (class) : 存 動畫作用的骨架名稱 和 3種Data的List
            Scale/Rotate/TransData (class) : 存 keyframe的time value curve

"""


def OutputJson(animationList, folder_path, file_name):

    skeleton = SkeletonInfo(folder_path)
    bones = BonesInfo()
    slots = SlotsInfo(file_name)
    skins = SkinsInfo(folder_path, file_name)
    anims = AnimationInfo(animationList)

    for ani_name, ani_data in anims.items():
        data = {
            "skeleton": skeleton,
            "bones": bones,
            "slots": slots,
            "skins": skins,
            "animations": {ani_name: ani_data},
        }
        json_filename = f"{ani_name}.json"
        save_json_path = os.path.join(JSON_FILE_FOLDER, json_filename)
        f = open(save_json_path, "w")  # create json file
        json.dump(data, f, indent=4)

    # data = {
    #     "skeleton": skeleton,
    #     "bones": bones,
    #     "slots": slots,
    #     "skins": skins,
    #     "animations": anims,
    # }
