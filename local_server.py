import pathlib
import zipfile
from flask import Flask, request, jsonify, send_file
import os
import subprocess
import pyautogui
import pygetwindow as gw
import ctypes
import time
import datetime
import json
import sys

SRC_PATH = pathlib.Path(__file__).parent.absolute()
sys.path.append(str(SRC_PATH))
sys.path.append(
    str(os.path.join(SRC_PATH, "HTML", "pythonFile"))
)  # ensure SRC_PATH is in sys.path
import selenium_control as seleniumControl

app = Flask(__name__, static_url_path="/static")
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

SPINE_FOLDER_PATH = os.path.join(CURRENT_DIR, "HTML", "spine")
UPLOAD_IMG_FOLDER = os.path.join(CURRENT_DIR, "HTML", "static", "Image", "Saved")
JSON_FILE_FOLDER = os.path.join(CURRENT_DIR, "HTML", "static", "JsonFile")
MAPPING_FILE_PATH = os.path.join(CURRENT_DIR, "HTML", "template_mapping.json")
WEBDOWNLOAD_FOLDER = os.path.join(CURRENT_DIR, "HTML", "static", "WebDownload")

GIF_BUTTON_IMG_PATH = os.path.join(
    CURRENT_DIR, "HTML", "static", "Image", "gif_button.png"
)
GIF_BUTTON_IMG_SE_PATH = os.path.join(
    CURRENT_DIR, "HTML", "static", "Image", "gif_button_selected.png"
)
SPINE_PROGRAM = "Spine.com"
SPINE_EXE = "Spine.exe"


def FindSpineProgram():
    # Start searching from the root directories
    potential_roots = ["E:\\"]
    valid_roots = [root for root in potential_roots if os.path.exists(root)]
    for root in valid_roots:
        for dirpath, dirnames, filenames in os.walk(root):
            if SPINE_PROGRAM in filenames:
                return os.path.join(dirpath, SPINE_PROGRAM)
    return None


def ChangeLanguageEng():
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    HKL_NEXT = 1
    LANG_ENGLISH_US = 0x0409
    HKL = ctypes.windll.user32.LoadKeyboardLayoutW(
        f"0000{LANG_ENGLISH_US:04X}", HKL_NEXT
    )
    ctypes.windll.user32.PostMessageW(hwnd, 0x50, 0, HKL)


def AdjustCurve(curve, intensity, indices, operation):
    for i in indices:
        if i < len(curve):
            if operation == "mul":
                curve[i] *= intensity
            elif operation == "div":
                curve[i] /= intensity
    return curve


def AdjustSpeed(json_data, speed):
    for animation_name, animation in json_data["animations"].items():
        for b_name, b_animation in animation["bones"].items():
            for transform_type in ["scale", "translate", "rotate"]:
                if transform_type in b_animation and b_animation[transform_type]:
                    for index, frame in enumerate(b_animation[transform_type]):
                        if "time" in frame:
                            frame["time"] /= speed
                        if (
                            "curve" in frame
                            and frame["curve"] != "stepped"
                            and frame["curve"]
                        ):
                            frame["curve"] = AdjustCurve(
                                frame["curve"], speed, [0, 2, 4, 6], "div"
                            )

    return json_data


def AdjustScale(json_data, intensity):
    for animation_name, animation in json_data["animations"].items():
        for b_name, b_animation in animation["bones"].items():
            if "scale" in b_animation and b_animation["scale"]:
                prev_x = b_animation["scale"][0].get("x", 1)
                prev_y = b_animation["scale"][0].get("y", 1)
                first_x = prev_x
                first_y = prev_y
                last_x = b_animation["scale"][-1].get("x", 1)
                last_y = b_animation["scale"][-1].get("y", 1)
                for index, frame in enumerate(b_animation["scale"]):
                    # skip first & last frame if value is the same (to keep animation continous)
                    if (index == 0 or index == len(b_animation["scale"]) - 1) and (
                        first_x == last_x and first_y == last_y
                    ):
                        continue

                    current_x = frame["x"]
                    current_y = frame["y"]

                    if current_x * prev_x >= 0:  # 同正or同負
                        # enhance x
                        if abs(current_x) >= abs(prev_x):
                            frame["x"] *= intensity
                            # adjust curve (current and previous frame)
                            if "curve" in frame and frame["curve"] != "stepped":
                                frame["curve"] = AdjustCurve(
                                    frame["curve"], intensity, [1], "mul"
                                )
                                if (
                                    index > 0
                                    and "curve" in b_animation["scale"][index - 1]
                                    and b_animation["scale"][index - 1]["curve"]
                                    != "stepped"
                                ):
                                    b_animation["scale"][index - 1]["curve"] = (
                                        AdjustCurve(
                                            b_animation["scale"][index - 1]["curve"],
                                            intensity,
                                            [3],
                                            "mul",
                                        )
                                    )
                        # weaken x
                        else:
                            frame["x"] /= intensity
                            # adjust curve (current and previous frame)
                            if "curve" in frame and frame["curve"] != "stepped":
                                frame["curve"] = AdjustCurve(
                                    frame["curve"], intensity, [1], "div"
                                )
                                if (
                                    index > 0
                                    and "curve" in b_animation["scale"][index - 1]
                                    and b_animation["scale"][index - 1]["curve"]
                                    != "stepped"
                                ):
                                    b_animation["scale"][index - 1]["curve"] = (
                                        AdjustCurve(
                                            b_animation["scale"][index - 1]["curve"],
                                            intensity,
                                            [3],
                                            "div",
                                        )
                                    )

                        if abs(frame["x"]) < 0.001:  # prevent scale=0
                            frame["x"] = 0.001 if frame["x"] > 0 else -0.01

                    else:  # 一正一負
                        frame["x"] *= intensity
                        # adjust curve (current and previous frame)
                        if "curve" in frame and frame["curve"] != "stepped":
                            frame["curve"] = AdjustCurve(
                                frame["curve"], intensity, [1], "mul"
                            )
                            if (
                                index > 0
                                and "curve" in b_animation["scale"][index - 1]
                                and b_animation["scale"][index - 1]["curve"]
                                != "stepped"
                            ):
                                b_animation["scale"][index - 1]["curve"] = AdjustCurve(
                                    b_animation["scale"][index - 1]["curve"],
                                    intensity,
                                    [3],
                                    "mul",
                                )
                        if abs(frame["x"]) < 0.001:  # prevent scale=0
                            frame["x"] = 0.001 if frame["x"] > 0 else -0.01

                    if current_y * prev_y >= 0:  # 同正or同負
                        # enhance y
                        if abs(current_y) >= abs(prev_y):
                            frame["y"] *= intensity
                            # adjust curve (current and previous frame)
                            if "curve" in frame and frame["curve"] != "stepped":
                                frame["curve"] = AdjustCurve(
                                    frame["curve"], intensity, [5], "mul"
                                )
                                if (
                                    index > 0
                                    and "curve" in b_animation["scale"][index - 1]
                                    and b_animation["scale"][index - 1]["curve"]
                                    != "stepped"
                                ):
                                    b_animation["scale"][index - 1]["curve"] = (
                                        AdjustCurve(
                                            b_animation["scale"][index - 1]["curve"],
                                            intensity,
                                            [7],
                                            "mul",
                                        )
                                    )
                        else:
                            frame["y"] /= intensity
                            # adjust curve (current and previous frame)
                            if "curve" in frame and frame["curve"] != "stepped":
                                frame["curve"] = AdjustCurve(
                                    frame["curve"], intensity, [5], "div"
                                )
                                if (
                                    index > 0
                                    and "curve" in b_animation["scale"][index - 1]
                                    and b_animation["scale"][index - 1]["curve"]
                                    != "stepped"
                                ):
                                    b_animation["scale"][index - 1]["curve"] = (
                                        AdjustCurve(
                                            b_animation["scale"][index - 1]["curve"],
                                            intensity,
                                            [7],
                                            "div",
                                        )
                                    )

                        if abs(frame["y"]) < 0.001:  # prevent scale=0
                            frame["y"] = 0.001 if frame["y"] > 0 else -0.01

                    else:  # 一正一負
                        frame["y"] *= intensity
                        # adjust curve (current and previous frame)
                        if "curve" in frame and frame["curve"] != "stepped":
                            frame["curve"] = AdjustCurve(
                                frame["curve"], intensity, [5], "mul"
                            )
                            if (
                                index > 0
                                and "curve" in b_animation["scale"][index - 1]
                                and b_animation["scale"][index - 1]["curve"]
                                != "stepped"
                            ):
                                b_animation["scale"][index - 1]["curve"] = AdjustCurve(
                                    b_animation["scale"][index - 1]["curve"],
                                    intensity,
                                    [7],
                                    "mul",
                                )
                        if abs(frame["x"]) < 0.001:  # prevent scale=0
                            frame["x"] = 0.001 if frame["x"] > 0 else -0.01

                    prev_x = current_x
                    prev_y = current_y
    return json_data


def AdjustTranslate(json_data, intensity):
    for animation_name, animation in json_data["animations"].items():
        for b_name, b_animation in animation["bones"].items():
            if "translate" in b_animation and b_animation["translate"]:
                first_x = b_animation["translate"][0].get("x", 0)
                first_y = b_animation["translate"][0].get("y", 0)
                last_x = b_animation["translate"][-1].get("x", 0)
                last_y = b_animation["translate"][-1].get("y", 0)
                for index, frame in enumerate(b_animation["translate"]):
                    # skip first & last frame if value is the same (to keep animation continous)
                    if (index == 0 or index == len(b_animation["translate"]) - 1) and (
                        first_x == last_x and first_y == last_y
                    ):
                        continue

                    frame["x"] *= intensity
                    frame["y"] *= intensity
                    # adjust curve (current and previous frame)
                    if "curve" in frame and frame["curve"] != "stepped":
                        frame["curve"] = AdjustCurve(
                            frame["curve"], intensity, [1, 3], "mul"
                        )
                        if (
                            index > 0
                            and "curve" in b_animation["translate"][index - 1]
                            and b_animation["translate"][index - 1]["curve"]
                            != "stepped"
                        ):
                            b_animation["translate"][index - 1]["curve"] = AdjustCurve(
                                b_animation["translate"][index - 1]["curve"],
                                intensity,
                                [5, 7],
                                "mul",
                            )
    return json_data


def AdjustRotate(json_data, intensity):
    for animation_name, animation in json_data["animations"].items():
        for b_name, b_animation in animation["bones"].items():
            if "rotate" in b_animation and b_animation["rotate"]:
                prev_value = b_animation["rotate"][0].get("value", 0)
                first_value = prev_value
                last_value = b_animation["rotate"][-1].get("value", 0)

                for index, frame in enumerate(b_animation["rotate"]):
                    # skip first & last frame if value is the same (to keep animation continous)
                    if (index == 0 or index == len(b_animation["rotate"]) - 1) and (
                        first_value == last_value
                    ):
                        continue

                    current_value = frame["value"]

                    if current_value * prev_value >= 0:  # 同正or同負
                        if abs(current_value) >= abs(prev_value):
                            frame["value"] *= intensity
                            # adjust curve (current and previous frame)
                            if "curve" in frame and frame["curve"] != "stepped":
                                frame["curve"] = AdjustCurve(
                                    frame["curve"], intensity, [1], "mul"
                                )
                                if (
                                    index > 0
                                    and "curve" in b_animation["rotate"][index - 1]
                                    and b_animation["rotate"][index - 1]["curve"]
                                    != "stepped"
                                ):
                                    b_animation["rotate"][index - 1]["curve"] = (
                                        AdjustCurve(
                                            b_animation["rotate"][index - 1]["curve"],
                                            intensity,
                                            [3],
                                            "mul",
                                        )
                                    )
                        else:
                            frame["value"] /= intensity
                            # adjust curve (current and previous frame)
                            if "curve" in frame and frame["curve"] != "stepped":
                                frame["curve"] = AdjustCurve(
                                    frame["curve"], intensity, [1], "div"
                                )
                                if (
                                    index > 0
                                    and "curve" in b_animation["rotate"][index - 1]
                                    and b_animation["rotate"][index - 1]["curve"]
                                    != "stepped"
                                ):
                                    b_animation["rotate"][index - 1]["curve"] = (
                                        AdjustCurve(
                                            b_animation["rotate"][index - 1]["curve"],
                                            intensity,
                                            [3],
                                            "div",
                                        )
                                    )
                    else:  # 一正一負
                        frame["value"] *= intensity
                        # adjust curve (current and previous frame)
                        if "curve" in frame and frame["curve"] != "stepped":
                            frame["curve"] = AdjustCurve(
                                frame["curve"], intensity, [1], "mul"
                            )
                            if (
                                index > 0
                                and "curve" in b_animation["rotate"][index - 1]
                                and b_animation["rotate"][index - 1]["curve"]
                                != "stepped"
                            ):
                                b_animation["rotate"][index - 1]["curve"] = AdjustCurve(
                                    b_animation["rotate"][index - 1]["curve"],
                                    intensity,
                                    [3],
                                    "mul",
                                )

                    if frame["value"] < 0:  # ensure angle won't exceed -360
                        while frame["value"] < -360:  # and keep value negative
                            frame["value"] += 360
                    else:
                        frame["value"] = frame["value"] % 360

                    prev_value = current_value
    return json_data


@app.route("/main_process", methods=["POST"])
def main_process():
    if "json_file" not in request.files or "image_file" not in request.files:
        return jsonify({"error": "Missing files"}), 400

    json_file = request.files["json_file"]
    image_file = request.files["image_file"]
    intensity_translate = float(request.form.get("intensityTranslate", 1.0))
    intensity_scale = float(request.form.get("intensityScale", 1.0))
    intensity_rotate = float(request.form.get("intensityRotate", 1.0))
    speed = float(request.form.get("speed", 1.0))

    output_gif_path = os.path.join(UPLOAD_IMG_FOLDER, "output_gif.gif")
    if json_file.filename == "" or image_file.filename == "":
        print("file error(local).\n")
        return jsonify({"error": "No selected files"}), 400

    # save json & image file to local path
    json_path = os.path.join(JSON_FILE_FOLDER, json_file.filename)
    json_file.save(json_path)
    # modify image folder path to ///local path/// in json file
    with open(json_path, "r") as j_file:
        json_data = json.load(j_file)
    json_data["skeleton"]["images"] = UPLOAD_IMG_FOLDER

    # adjust animation factor
    if intensity_scale != 1.0:
        json_data = AdjustScale(json_data, intensity_scale)
    if intensity_translate != 1.0:
        json_data = AdjustTranslate(json_data, intensity_translate)
    if intensity_rotate != 1.0:
        json_data = AdjustRotate(json_data, intensity_rotate)
    if speed != 1.0:
        json_data = AdjustSpeed(json_data, speed)

    with open(json_path, "w") as j_file:
        json.dump(json_data, j_file, indent=4)

    image_path = os.path.join(UPLOAD_IMG_FOLDER, image_file.filename)
    image_file.save(image_path)

    # launch Spine CLI to export .spine file from animation.json
    spine_path = FindSpineProgram()
    now = datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=8)))
    timeslot = now.strftime("%Y%m%d%H%M%S")  # yyyymmddhhmmss
    output_spine_name = "output" + timeslot + ".spine"
    spine_file_path = os.path.join(SPINE_FOLDER_PATH, output_spine_name)
    print(f"json path: {json_path}\n")
    print(f"spine file path: {spine_file_path}\n")
    subprocess.run(
        [
            spine_path,
            "--update",
            "4.2.20",  # version
            "-i",
            json_path,  # input json file
            "-o",
            spine_file_path,  # output spine file
            "-r",
        ],
        check=True,
    )
    # change spine program from .com to .exe
    spine_folder_path, file_name = os.path.split(spine_path)
    spine_path = os.path.join(spine_folder_path, SPINE_EXE)
    time.sleep(1)
    # open spine file in Spine GUI
    subprocess.Popen([spine_path, spine_file_path, "--auto-start"])
    print("Spine launched successfully.")
    time.sleep(9)

    return GenerateGIF(output_gif_path)
    # retries = 5
    # while retries > 0:
    #     windows = gw.getWindowsWithTitle("Spine - output")
    #     if windows:
    #         try:
    #             spine_window = windows[0]
    #             spine_window.activate()
    #             time.sleep(0.5)
    #             pyautogui.hotkey("ctrl", "e")
    #             ChangeLanguageEng()
    #             # pyautogui.click(x=327, y=422)
    #             time.sleep(1)
    #             # click GIF button
    #             gif_button_location = None
    #             try:
    #                 gif_button_location = pyautogui.locateOnScreen(GIF_BUTTON_IMG_PATH)
    #                 if gif_button_location is not None:
    #                     gif_button_location = pyautogui.center(gif_button_location)
    #                     time.sleep(0.5)
    #                     pyautogui.click(gif_button_location)
    #                     pyautogui.click(gif_button_location)
    #                     time.sleep(0.5)
    #                 else:
    #                     print("GIF radio button not found, trying alternate image.")
    #             except Exception as e:
    #                 print(f"Failed to find GIF button with first image: {e}")

    #             if gif_button_location is None:
    #                 try:
    #                     gif_button_location = pyautogui.locateOnScreen(
    #                         GIF_BUTTON_IMG_SE_PATH
    #                     )
    #                     if gif_button_location is not None:
    #                         print(" GIF radio button_SE found.")
    #                         gif_button_location = pyautogui.center(gif_button_location)
    #                         time.sleep(0.5)
    #                         pyautogui.click(gif_button_location)
    #                         pyautogui.click(gif_button_location)
    #                         time.sleep(0.5)
    #                     else:
    #                         print("Alternate GIF radio button not found.")
    #                         raise Exception("GIF radio button not found")
    #                 except Exception as e:
    #                     print(f"Failed to find GIF button with second image: {e}")
    #                     return jsonify({"error": "GIF button not found"}), 500

    #             # Press Tab key to switch to the textbox
    #             pyautogui.press("tab")
    #             time.sleep(0.5)
    #             pyautogui.write(output_gif_path, interval=0.04)
    #             time.sleep(0.5)

    #             # Press Enter to finish the export
    #             pyautogui.press("enter")
    #             time.sleep(0.5)
    #             pyautogui.press("enter")
    #             time.sleep(3)
    #             break
    #         except Exception as e:
    #             print(f"Failed to activate Spine window: {e}")
    #             time.sleep(1)
    #     retries -= 1
    #     print(f"Retrying... ({5 - retries}/5)")
    # if retries == 0:
    #     return jsonify({"error": "Failed to activate Spine window"}), 500
    # with open(output_gif_path, "rb") as gif_file:
    #     gif_data = gif_file.read()

    # return gif_data, 200, {"Content-Type": "image/gif"}


@app.route("/mesh_process", methods=["POST"])
def mesh_process():
    if "json_file" not in request.files or "image_file" not in request.files:
        return jsonify({"error": "Missing files"}), 400

    json_file = request.files["json_file"]
    image_file = request.files["image_file"]
    output_gif_path = os.path.join(UPLOAD_IMG_FOLDER, "output_gif.gif")
    if json_file.filename == "" or image_file.filename == "":
        print("file error(local).\n")
        return jsonify({"error": "No selected files"}), 400

    # save json & image file to local path
    json_path = os.path.join(JSON_FILE_FOLDER, json_file.filename)
    json_file.save(json_path)

    # modify image folder path to ///local path/// in json file
    with open(json_path, "r") as j_file:
        json_data = json.load(j_file)
    json_data["skeleton"]["images"] = UPLOAD_IMG_FOLDER
    with open(json_path, "w") as j_file:
        json.dump(json_data, j_file, indent=4)

    image_path = os.path.join(UPLOAD_IMG_FOLDER, image_file.filename)
    image_file.save(image_path)

    # launch Spine CLI to export .spine file from animation.json
    spine_path = FindSpineProgram()
    now = datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=8)))
    timeslot = now.strftime("%Y%m%d%H%M%S")  # yyyymmddhhmmss
    output_spine_name = "output" + timeslot + ".spine"
    spine_file_path = os.path.join(SPINE_FOLDER_PATH, output_spine_name)
    print(f"json path: {json_path}\n")
    print(f"spine file path: {spine_file_path}\n")
    subprocess.run(
        [
            spine_path,
            "--update",
            "4.2.20",  # version
            "-i",
            json_path,  # input json file
            "-o",
            spine_file_path,  # output spine file
            "-r",
        ],
        check=True,
    )
    # change spine program from .com to .exe
    spine_folder_path, file_name = os.path.split(spine_path)
    spine_path = os.path.join(spine_folder_path, SPINE_EXE)
    time.sleep(1)
    # open spine file in Spine GUI
    subprocess.Popen([spine_path, spine_file_path, "--auto-start"])
    print("Spine launched successfully.")
    time.sleep(9)
    return GenerateGIF(output_gif_path)


@app.route("/mapping_process", methods=["POST"])
def mapping_process():
    print("Request received for /mapping_process")
    if "json_file" not in request.files:
        return jsonify({"error": "Missing files"}), 400

    json_file = request.files["json_file"]
    json_file.save(MAPPING_FILE_PATH)
    return "File saved successfully", 200


@app.route("/game_url_process", methods=["POST"])
def game_url_process():
    print("Request received for /game_url_process")
    game_url = request.form["game_url"]
    try:
        seleniumControl.SetUrl(game_url)
        files_dir = seleniumControl.main()
        if files_dir is not None:
            # compress folder's files
            z_file = os.path.join(WEBDOWNLOAD_FOLDER, "resources.zip")
            with zipfile.ZipFile(z_file, "w") as zipf:
                for file_name in os.listdir(files_dir):
                    f_path = os.path.join(files_dir, file_name)
                    if os.path.isfile(f_path):
                        zipf.write(f_path, arcname=file_name)
            print("Compress complete\n")
            if os.path.exists(z_file):
                return send_file(z_file, as_attachment=True)
            else:
                print("Cannot find zip file at local.\n")
        else:
            print("Selenium control failed\n")

    except Exception as e:
        return jsonify({"error": "Missing files"}), 400


# control spine to export gif and return
def GenerateGIF(output_gif_path):
    retries = 5
    while retries > 0:
        windows = gw.getWindowsWithTitle("Spine - output")
        if windows:
            try:
                spine_window = windows[0]
                spine_window.activate()
                time.sleep(0.5)
                pyautogui.hotkey("enter")
                pyautogui.hotkey("ctrl", "e")
                ChangeLanguageEng()
                # pyautogui.click(x=327, y=422)
                time.sleep(0.5)
                # click GIF button
                gif_button_location = None
                try:
                    gif_button_location = pyautogui.locateOnScreen(GIF_BUTTON_IMG_PATH)
                    if gif_button_location is not None:
                        gif_button_location = pyautogui.center(gif_button_location)
                        time.sleep(0.5)
                        pyautogui.click(gif_button_location)
                        pyautogui.click(gif_button_location)
                        time.sleep(0.5)
                    else:
                        print("GIF radio button not found, trying alternate image.")
                except Exception as e:
                    print(f"Failed to find GIF button with first image: {e}")

                if gif_button_location is None:
                    try:
                        gif_button_location = pyautogui.locateOnScreen(
                            GIF_BUTTON_IMG_SE_PATH
                        )
                        if gif_button_location is not None:
                            print(" GIF radio button_SE found.")
                            gif_button_location = pyautogui.center(gif_button_location)
                            time.sleep(0.5)
                            pyautogui.click(gif_button_location)
                            pyautogui.click(gif_button_location)
                            time.sleep(0.5)
                        else:
                            print("Alternate GIF radio button not found.")
                            raise Exception("GIF radio button not found")
                    except Exception as e:
                        print(f"Failed to find GIF button with second image: {e}")
                        return jsonify({"error": "GIF button not found"}), 500

                # Press Tab key to switch to the textbox
                pyautogui.press("tab")
                time.sleep(0.5)
                pyautogui.write(output_gif_path, interval=0.04)
                time.sleep(0.5)

                # Press Enter to finish the export
                pyautogui.press("enter")
                time.sleep(0.5)
                pyautogui.press("enter")
                time.sleep(3)
                break
            except Exception as e:
                print(f"Failed to activate Spine window: {e}")
                time.sleep(1)
        retries -= 1
        print(f"Retrying... ({5 - retries}/5)")
    if retries == 0:
        return jsonify({"error": "Failed to activate Spine window"}), 500
    with open(output_gif_path, "rb") as gif_file:
        gif_data = gif_file.read()

    return gif_data, 200, {"Content-Type": "image/gif"}


if __name__ == "__main__":
    app.run(port=5001)
