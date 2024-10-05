import json
import glob
import os
import re
import shutil

config_folder_path = r"C:\Users\cyivs\OneDrive\Desktop\Slot_asset\Fetch_From_Web\slotcatalog.com (1)\static.pgsoft-games.com\126\assets\resources"
root_dir = ""
saved_dir = (
    r"C:\Users\cyivs\OneDrive\Desktop\Spine_Project\HTML\static\WebDownload\FetchFiles"
)


def SetFolderPath(input_path):
    global root_dir
    root_dir = input_path


"""
0. 找config.json
    檢查types裡有沒有"sp.SkeletonData"
"""


def FetchConfig():
    global config_folder_path
    config_file = None
    # find config json file
    file_pattern = os.path.join(root_dir, f"**/config.*.json")
    matching_files = glob.glob(file_pattern, recursive=True)

    # find config which has skeletonData
    for file in matching_files:
        with open(file, "r", encoding="utf-8") as f:
            c_data = json.load(f)
            if "types" in c_data and "sp.SkeletonData" in c_data["types"]:
                config_file = file
                config_folder_path = os.path.dirname(config_file)
                break

    return config_file


def CheckConfig(config_data):

    if "sp.SkeletonData" in config_data["types"]:
        return config_data["types"].index("sp.SkeletonData")
    return -1


"""
1. 找動畫json檔
    1-1. 從config找"path", spine/..._atlas_... 的都是動畫檔名
    1-2. 用動畫檔名對應的編號, 到"version"的"import"找, 編號的下一個data就是動畫原始檔名 ...abc12d.json
    1-3. 用原始檔名*abc12d.json, 到import資料夾找出真正的檔案(animation.json)
"""


def FetchAllSpineFile(config_data, skeleton_index):

    matching_paths = []
    for key, value in config_data["paths"].items():
        # spine file name format = spine/***_atlas_***
        if re.search(r"spine/.*_atlas", value[0]) and value[1] == skeleton_index:
            matching_paths.append(key)

    # search key is in "import" folder or not
    version_import = config_data["versions"]["import"]
    original_filename_list = []
    for key in matching_paths:
        try:
            key_index = version_import.index(int(key))
            # spine json file's (partial) name follows the key
            original_filename_list.append(version_import[key_index + 1])

        except ValueError:
            print(f"Key {key} does not in import list")
            original_filename_list.append(0)

    # search json file's (entire) name in import folder
    import_folder_path = os.path.join(config_folder_path, "import")
    found_json_files = []
    for key in original_filename_list:
        # search all children folder (use **)
        file_pattern = os.path.join(import_folder_path, f"**/*.{key}.json")
        matching_files = glob.glob(file_pattern, recursive=True)
        if matching_files:
            found_json_files.extend(matching_files)
        else:
            print(f"Cannot find json file ends with {key}.")

    print(f"existing json files:")
    for file_path in found_json_files:
        print(f"{file_path}")

    return found_json_files


"""
2. 找動畫素材png檔
    1-1. 從animation.json找第二筆資料(中括號), uuid(可能有複數個png檔)
    1-2. 到config查uuid, 看是第幾個uuid(start from 0), 取得編號
    1-3. 找編號在不在"version"的"native"裡, 編號的下一個data就是png原始檔名 ...123abc.png
    1-4. 用原始檔名*123abc.png, 到native資料夾找出真正的檔案(symbols.png, symbols2.png,... 對應動畫json中的textureNames順序)
"""


def FetchPngAsset(config_data, animation_json_paths):

    animation_png_list = []  # 2d-list
    for anim_json in animation_json_paths:
        with open(anim_json, "r", encoding="utf-8") as file:
            anim_data = json.load(file)
            if anim_data[3][0][0] != "sp.SkeletonData":
                print(f"{anim_json}\nis not spine file.")
                continue

            # data_format = anim_data[3][0][2]
            uuids = anim_data[1]  # uuid[]
            original_pngname_list = []
            for uuid in uuids:
                try:
                    uuid_index = config_data["uuids"].index(uuid)
                    # search key is in "native" folder or not
                    version_native = config_data["versions"]["native"]
                    try:
                        key_index = version_native.index(int(uuid_index))
                        # png file's (partial) name follows the key(uuid_index)
                        original_pngname_list.append(version_native[key_index + 1])

                    except ValueError:
                        print(f"uuid index {uuid_index} does not in native list")

                except ValueError:
                    print(f"Cannot find uuid {uuid} 's index.")
            # search json file's (entire) name in import folder
            native_folder_path = os.path.join(config_folder_path, "native")
            found_png_files = []
            for key in original_pngname_list:
                # search all children folder (use **)
                file_pattern = os.path.join(native_folder_path, f"**/*.{key}.png")
                matching_files = glob.glob(file_pattern, recursive=True)
                if matching_files:
                    found_png_files.extend(matching_files)
                else:
                    print(f"Cannot find png file ends with {key}.")

            animation_png_list.append(found_png_files)

            print(f"existing png files for{anim_json}:")
            for file_path in found_png_files:
                print(f"{file_path}")
    return animation_png_list


def ChangePngNames(png_2d_list, name_2d_list):
    if len(png_2d_list) != len(name_2d_list):
        print("Error: all png file amount doesn't match name list")
        return
    for png_list, name_list in zip(png_2d_list, name_2d_list):
        if len(png_list) != len(name_list):
            print("Error: png file amount doesn't match name list")
            return
        for png_file, new_name in zip(png_list, name_list):
            try:
                new_name_path = os.path.join(saved_dir, new_name)
                shutil.copy(png_file, new_name_path)
                print(f"png {png_file} saved as {new_name_path}")
            except FileNotFoundError:
                print(f"Error: cannot fild png {png_file}")
            except Exception as e:
                print(f"Error: copy {png_file} failed: {e}")


"""
3. 檢查動畫json
    1-1. 從animation.json找第四筆資料(中括號)的第一筆資料(中括號), 檢查第一筆資料是否為"sp.SkeletonData"
    1-2. 中括號內的中括號，第二筆資料[...]為底下資料對應的資訊名稱
        1-2-1. "_name" spine檔名(string)
        1-2-2. "_atlasText" 拆圖atlas文字, \n要代換成regular expression(string)
        1-2-3. "textureNames" 圖檔使用的名稱(要確定跟atlas的開頭png檔名是否相同)(["string"])
        1-2-4. "_skeletonJson" spine json檔案格式內容({...})
        以上在第六筆資料(中括號)的第一筆資料(中括號), 略過第一筆資料(某數字)開始取
"""


def FindSkeletonIndexInData(data, current_index=None):

    if current_index is None:
        current_index = []
    if isinstance(data, dict):
        if "skeleton" in data:
            return current_index  # skeleton data found
        # skeleton info won't be in the dict of dict
    elif isinstance(data, list):
        for index, item in enumerate(data):
            result = FindSkeletonIndexInData(item, current_index + [index])
            if result is not None:
                return result  # skeleton data found
    return None


def FetchAnimationInfo(config_data, animation_json_paths):

    spine_json_list = []
    png_name_2d_list = []
    for anim_json in animation_json_paths:
        with open(anim_json, "r", encoding="utf-8") as file:
            anim_data = json.load(file)
            # find spine data in json
            skeleton_index = FindSkeletonIndexInData(anim_data)  # [5][0][4]
            if skeleton_index:
                # print(f"skeleton info found at: {skeleton_index}")
                # get spine json data
                skeleton_data = anim_data
                for key in skeleton_index:
                    skeleton_data = skeleton_data[key]
                # print(f"skeleton hash: {skeleton_data["skeleton"]["hash"]}")

                # get spine json original file name
                filename_index = skeleton_index.copy()
                filename_index[-1] -= 3  # [5][0][1]
                fillename_data = anim_data
                for key in filename_index:
                    fillename_data = fillename_data[key]
                new_spine_json_name = f"{fillename_data}.json"

                new_spine_json_name = os.path.join(saved_dir, new_spine_json_name)

                with open(new_spine_json_name, "w", encoding="utf-8") as output_file:
                    json.dump(skeleton_data, output_file, indent=4)
                spine_json_list.append(new_spine_json_name)
                print(f"json file saved: {new_spine_json_name}")

                # get atlas file text
                atlas_info_index = filename_index.copy()
                atlas_info_index[-1] += 1  # [5][0][2]
                atlas_data = anim_data
                for key in atlas_info_index:
                    atlas_data = atlas_data[key]
                atlas_data = atlas_data.replace("\\n", "\n")
                atlas_filename = f"{fillename_data}.atlas"

                atlas_filename = os.path.join(saved_dir, atlas_filename)

                with open(atlas_filename, "w", encoding="utf-8") as output_file:
                    output_file.write(atlas_data)
                print(f"atlas file saved: {atlas_filename}")

                # process png filename list (return)
                png_info_index = atlas_info_index.copy()
                png_info_index[-1] += 1  # [5][0][3]
                png_name_list = anim_data
                for key in png_info_index:
                    png_name_list = png_name_list[key]
                png_name_2d_list.append(png_name_list)
            else:
                print("skeleton not found")

    return spine_json_list, png_name_2d_list


def main():

    # find config json file
    config_file = FetchConfig()
    if config_file is None:
        print("Failed to find config.json")
        return None
    print(f"config file name: {config_file}")
    with open(config_file, "r", encoding="utf-8") as file:
        config_data = json.load(file)

        skeleton_index = CheckConfig(config_data)
        if skeleton_index < 0:
            print("Cannot find skeleton info in this config.")
            return None  # error
        animation_json_paths = FetchAllSpineFile(config_data, skeleton_index)  # 1d-list
        animation_png_list = FetchPngAsset(config_data, animation_json_paths)  # 2d-list
        spine_json_list, png_name_list = FetchAnimationInfo(
            config_data, animation_json_paths
        )  # spine json file names 1d-list, png name 2d-list
        ChangePngNames(animation_png_list, png_name_list)
        # for png_list in animation_png_list:
        #     print(png_list)
        return saved_dir


if __name__ == "__main__":
    main()
