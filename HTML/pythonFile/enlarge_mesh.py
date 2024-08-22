import json
import os
from PIL import Image


input_img_path = r"C:\Users\cyivs\OneDrive\Desktop\Slot_asset\JQK拆原圖\As.png"
output_img_path = r"C:\Users\cyivs\OneDrive\Desktop\Slot_asset\JQK拆原圖\As_enlarge.png"

input_json_path = (
    r"C:\Users\cyivs\OneDrive\Desktop\Slot_asset\gloves\h_gloves_atlas_symbols.json"
)
output_json_path = r"C:\Users\cyivs\OneDrive\Desktop\Slot_asset\gloves\h_gloves_atlas_symbols_modify.json"
scale_factor = 2


class Bone:
    def __init__(self, name, x=0, y=0, parent=None):
        self.name = name
        self.x = x  # absolute pos
        self.y = y  # absolute pos
        self.parent = parent

    def __repr__(self):
        return (
            f"Bone(name='{self.name}', x={self.x}, y={self.y}, parent='{self.parent}')"
        )


def IsValidPath(file_path, expected_extension):
    return os.path.isfile(file_path) and file_path.lower().endswith(expected_extension)


def SetJsonPath(input_path):
    global input_json_path, output_json_path
    input_json_path = input_path
    directory = os.path.dirname(input_json_path)
    filename = os.path.basename(input_json_path)
    new_filename = filename.replace(".json", "_modify.json")
    output_json_path = os.path.join(directory, new_filename)


def SetImgPath(input_path):
    global input_img_path, output_img_path
    input_img_path = input_path
    directory = os.path.dirname(input_img_path)
    filename = os.path.basename(input_img_path)
    new_filename = filename.replace(".png", "_enlarge.png")
    output_img_path = os.path.join(directory, new_filename)
    EnlargeImage()


def SetScale(input_factor):
    global scale_factor
    scale_factor = input_factor


def EnlargeImage():
    origin_img = Image.open(input_img_path)
    origin_size = origin_img.size
    new_size = (int(origin_size[0] * scale_factor), int(origin_size[1] * scale_factor))
    new_img = Image.new("RGBA", new_size, (0, 0, 0, 0))

    tlx = (new_size[0] - origin_size[0]) // 2
    tly = (new_size[1] - origin_size[1]) // 2

    new_img.paste(origin_img, (tlx, tly))
    new_img.save(output_img_path)
    print(f"Image saved to: {output_img_path}")


def ExtractBones(spine_data):
    bone_list = []
    for bone in spine_data["bones"]:
        name = bone["name"]
        x = bone.get("x", 0)  # relative pos
        y = bone.get("y", 0)
        p_name = bone.get("parent", None)
        if p_name is not None:  # parent一定會出現在child之前，必定在list裡
            p_x, p_y = ExtractParentPos(bone_list, p_name)
            x += p_x  # absolute pos
            y += p_y

        bone_list.append(Bone(name, x, y, p_name))

    return bone_list


def ExtractParentPos(bone_list, p_name):
    # search bone_list
    for bone in bone_list:
        if bone.name == p_name:
            return bone.x, bone.y
    return 0, 0  # doesn't fine parent (json error)


def GetBonePos(bone_list, b_index):
    if 0 <= b_index < len(bone_list):
        bone = bone_list[b_index]
        return bone.x, bone.y
    return 0, 0  # error


def EnlargeMesh(bone_list, mesh):
    vertices = mesh["vertices"]
    abs_x_list = []
    abs_y_list = []
    b_index_list = []  # vertex對應的權重骨骼編號
    i = 0
    while i < len(vertices):
        num_bones = vertices[i]  # number of bones which has weight on mesh
        i += 1
        for _ in range(num_bones):
            b_index = vertices[i]
            rel_x = vertices[i + 1]  # vertex's relative position
            rel_y = vertices[i + 2]
            # b_weight=vertices[i+3]

            bx, by = GetBonePos(bone_list, b_index)
            abs_x = bx + rel_x  # vertex's absolute position
            abs_y = by + rel_y

            abs_x_list.append(abs_x)
            abs_y_list.append(abs_y)
            b_index_list.append(b_index)

            i += 4

    # compute abs center
    cx = sum(abs_x_list) / len(abs_x_list)
    cy = sum(abs_y_list) / len(abs_y_list)
    # enlarge vertices abs pos
    for index in range(len(abs_x_list)):
        abs_x_list[index] = cx + (abs_x_list[index] - cx) * scale_factor
        abs_y_list[index] = cy + (abs_y_list[index] - cy) * scale_factor
    # compute vertices relative pos
    i = 0
    index = 0
    while i < len(vertices):
        num_bones = vertices[i]  # number of bones which has weight on mesh
        i += 1
        for _ in range(num_bones):
            # b_index = vertices[i]
            # 計算相對於基準骨骼的座標(rel)存回vertices
            bx, by = GetBonePos(bone_list, b_index_list[index])  # vertex骨骼座標(abs)
            vertices[i + 1] = abs_x_list[index] - bx  # vertex的相對座標(rel)
            vertices[i + 2] = abs_y_list[index] - by
            # b_weight = vertices[i+3]
            index += 1
            i += 4

    return vertices


def main():

    with open(input_json_path, "r", encoding="utf-8") as file:
        spine_data = json.load(file)

        # 歷遍所有vertices
        # 根據b_number去找基準點座標，把vertices相對座標轉換成絕對座標
        # 絕對座標和對應的b_number(方便後面查詢)存入新vertices_list
        # 計算中心點的絕對座標
        # 放大所有vertices的絕對座標(ABS)
        # 根據每個vertices的基準點(Bone_list[n]的x,y (ORI))回算相對位置(ABS-ORI=REL)

        bone_list = ExtractBones(spine_data)  # bone's number 0 ~ n-1

        for skin in spine_data.get("skins", []):
            if "attachments" in skin:
                for attachment_key, attachment in skin["attachments"].items():
                    for mesh_name, mesh in attachment.items():
                        if (
                            "type" in mesh
                            and mesh["type"] == "mesh"
                            and "vertices" in mesh
                        ):

                            mesh["vertices"] = EnlargeMesh(bone_list, mesh)
        # change image folder
        if "skeleton" in spine_data:
            spine_data["skeleton"]["images"] = os.path.dirname(output_img_path)
        # change slot's attachment
        for slot in spine_data.get("slots", []):
            if "attachment" in slot:
                old_attachment = slot["attachment"]
                new_attachment = os.path.basename(output_img_path)
                slot["attachment"] = new_attachment
                # print(
                #     f"Update attachment in slot from {old_attachment} to {new_attachment}"
                # )
        # change skins' attachment
        img_name = os.path.basename(output_img_path)
        for skin in spine_data.get("skins", []):
            if "attachments" in skin:
                for attachment_key, attachment in skin["attachments"].items():
                    for old_attachment_name in list(attachment.keys()):
                        attachment[img_name] = attachment.pop(old_attachment_name)
                        # print(
                        #     f"Update attachment in skin from {old_attachment_name} to {img_name}"
                        # )

    with open(output_json_path, "w") as file:
        json.dump(spine_data, file, indent=4)
    print(f"Json file saved to: {output_json_path}")
    return output_json_path


if __name__ == "__main__":
    main()
