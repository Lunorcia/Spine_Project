from flask import Flask, render_template, request, url_for, redirect
import pathlib
import sys
import os
import subprocess
import time
import pyautogui
import pygetwindow as gw
import ctypes
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# import pythonFile.mesh as mesh
import pythonFile.animate as animate

SRC_PATH = pathlib.Path(__file__).parent.absolute()  # (web.py)'s parent path = /HTML
# src = (absolute path)\HTML
# location of img file which user upload
UPLOAD_IMG_FOLDER = os.path.join(SRC_PATH, "static", "Image", "Saved")

GIF_BUTTON_IMG_PATH = os.path.join(SRC_PATH, "static", "Image", "gif_button.png")
GIF_BUTTON_IMG_SE_PATH = os.path.join(
    SRC_PATH, "static", "Image", "gif_button_selected.png"
)

JSON_FILE_FOLDER = os.path.join(SRC_PATH, "static", "JsonFile")
UPLOADED_JSON_FILE_FOLDER = os.path.join(SRC_PATH, "static", "UploadedJson")

SPINE_PROGRAM = "Spine.com"
SPINE_EXE = "Spine.exe"

TEMPLATE_MAPPING = {
    "Only Scale": {
        "Sym_bomp_01": os.path.join(JSON_FILE_FOLDER, "Sym_bomp_01.json"),
        "Sym_bomp_02": os.path.join(JSON_FILE_FOLDER, "Sym_bomp_02.json"),
        "Sym_Tip_01": os.path.join(JSON_FILE_FOLDER, "Sym_Tip_01.json"),
    },
    "Scale & rotate": {
        "01win": os.path.join(JSON_FILE_FOLDER, "01win.json"),
        "Sym_Cascading_01": os.path.join(JSON_FILE_FOLDER, "Sym_Cascading_01.json"),
        "Sym_bomp_03": os.path.join(JSON_FILE_FOLDER, "Sym_bomp_03.json"),
        "Sym_bomp_06": os.path.join(JSON_FILE_FOLDER, "Sym_bomp_06.json"),
        "Sym_bomp_07": os.path.join(JSON_FILE_FOLDER, "Sym_bomp_07.json"),
    },
    "Scale & translate": {
        "Sym_Cascading_02": os.path.join(JSON_FILE_FOLDER, "Sym_Cascading_02.json"),
        "Sym_bomp_04": os.path.join(JSON_FILE_FOLDER, "Sym_bomp_04.json"),
        "Sym_bomp_05": os.path.join(JSON_FILE_FOLDER, "Sym_bomp_05.json"),
    },
}


app = Flask(__name__)


def FindSpineProgram():
    # Start searching from the root directories
    potential_roots = ["E:\\"]
    valid_roots = [
        root for root in potential_roots if os.path.exists(root)
    ]  # check disk name exist or not
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


@app.route("/")
def index():
    print("route/")
    return render_template(
        "anim.html", image_web_url="", gif_web_url="", templates=TEMPLATE_MAPPING
    )


@app.route("/add_template_page")
def add_template_page():
    return render_template("add_template.html", templates=TEMPLATE_MAPPING)


@app.route("/upload", methods=["POST"])
def upload():
    # 取得表單中的參數值
    uploaded_image = request.files["image"]
    selected_letter = request.form["letter"]
    selected_template = request.form["template"]
    selected_type = request.form["animationType"]
    # 進行進一步的處理，例如將圖片保存到伺服器或進行其他操作
    uploaded_image.save(os.path.join(UPLOAD_IMG_FOLDER, uploaded_image.filename))
    img_url = f"/Image/Saved/{uploaded_image.filename}"  # /static written in html
    saved_img_path = os.path.join(UPLOAD_IMG_FOLDER, uploaded_image.filename)

    # generate json file
    # mesh.SetImgPath(saved_img_path)
    # mesh.main()
    # choose json file
    # choose template json
    type_dict = TEMPLATE_MAPPING.get(selected_type)
    template_json_path = type_dict.get(selected_template)
    saved_json_path = ""
    if not template_json_path or not os.path.exists(template_json_path):
        print("template doesn't exist\n")
        json_filename = "animation.json"
        saved_json_path = os.path.join(JSON_FILE_FOLDER, json_filename)
    else:
        print(f"template path: {template_json_path}\n")
        saved_json_path = template_json_path

    # prefix = selected_template[:3]
    # if prefix == "Sym":
    #     prefix = "sym"
    # else:
    #     prefix = prefix[:2]

    animate.SetImgPath(saved_img_path)
    animate.SetJsonFile(saved_json_path)
    animate.main()

    # launch Spine from cmd
    spine_path = FindSpineProgram()
    if spine_path:
        print(f"spine path = {spine_path}")
        try:
            # launch Spine CLI to export .spine file from animation.json
            now = datetime.datetime.now(
                tz=datetime.timezone(datetime.timedelta(hours=8))
            )
            timeslot = now.strftime("%Y%m%d%H%M%S")  # yyyymmddhhmmss
            spine_file_path = os.path.join(SRC_PATH, "spine")
            output_spine_name = "output" + timeslot + ".spine"
            spine_file_path = os.path.join(spine_file_path, output_spine_name)

            # spine_file_path = "E:/testSpine/output" + timeslot + ".spine"

            subprocess.run(
                [
                    spine_path,
                    "--update",
                    "4.2.20",  # version
                    "-i",
                    saved_json_path,  # input json file
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
            time.sleep(10)

            retries = 5
            while retries > 0:
                windows = gw.getWindowsWithTitle("Spine - output")
                if windows:
                    try:
                        spine_window = windows[0]
                        spine_window.activate()
                        time.sleep(0.5)
                        # spine_window.maximize()
                        # time.sleep(0.5)
                        pyautogui.hotkey("ctrl", "e")
                        ChangeLanguageEng()
                        pyautogui.click(x=327, y=422)
                        time.sleep(1)
                        # click GIF button
                        gif_button_location = None
                        try:
                            gif_button_location = pyautogui.locateOnScreen(
                                GIF_BUTTON_IMG_PATH
                            )
                            time.sleep(0.5)
                            if gif_button_location is not None:
                                print("GIF radio button found.")
                                gif_button_location = pyautogui.center(
                                    gif_button_location
                                )
                                time.sleep(0.5)
                                pyautogui.click(gif_button_location)
                                pyautogui.click(gif_button_location)
                                time.sleep(0.5)
                            else:
                                print(
                                    "GIF radio button not found, trying alternate image."
                                )
                        except Exception as e:
                            print(f"Failed to find GIF button with first image: {e}")

                        if gif_button_location is None:
                            try:
                                gif_button_location = pyautogui.locateOnScreen(
                                    GIF_BUTTON_IMG_SE_PATH
                                )
                                time.sleep(0.5)
                                if gif_button_location is not None:
                                    print(" GIF radio button_SE found.")
                                    gif_button_location = pyautogui.center(
                                        gif_button_location
                                    )
                                    time.sleep(0.5)
                                    pyautogui.click(gif_button_location)
                                    pyautogui.click(gif_button_location)
                                    time.sleep(0.5)

                                else:
                                    print("Alternate GIF radio button not found.")
                                    raise Exception("GIF radio button not found")
                            except Exception as e:
                                print(
                                    f"Failed to find GIF button with second image: {e}"
                                )

                        # Press Tab key to switch to the textbox
                        pyautogui.press("tab")
                        time.sleep(0.5)
                        # Insert the output path, type speed = 0.1 w/s
                        output_gif_path = os.path.join(
                            UPLOAD_IMG_FOLDER, "output_gif.gif"
                        )
                        pyautogui.write(output_gif_path, interval=0.05)
                        time.sleep(0.5)
                        # Press Enter to finish the export
                        pyautogui.press("enter")
                        time.sleep(0.5)
                        pyautogui.press("enter")
                        time.sleep(1)
                        break
                    except Exception as e:
                        print(f"Failed to activate Spine window: {e}")
                        time.sleep(1)
                retries -= 1
                print(f"Retrying... ({5 - retries}/5)")
            if retries == 0:
                print("Failed to activate Spine window after multiple retries.")

        except subprocess.CalledProcessError as e:
            print(f"Failed to launch Spine: {e}")
    else:
        print("Spine executable not found.")
    time.sleep(1)
    output_gif_path = os.path.join(UPLOAD_IMG_FOLDER, "output_gif.gif")
    if os.path.exists(output_gif_path):
        print("return img and gif")
        gif_path, gif_file_name = os.path.split(output_gif_path)
        gif_url = f"/Image/Saved/{gif_file_name}"  # /static written in html
        return render_template(
            "anim.html",
            image_web_url=img_url,
            gif_web_url=gif_url,
            templates=TEMPLATE_MAPPING,
        )
    # print("/upload/post")
    else:
        print("return img only")
        return render_template(
            "anim.html",
            image_web_url=img_url,
            gif_web_url="",
            templates=TEMPLATE_MAPPING,
        )


@app.route("/add_template", methods=["POST"])
def add_template():
    existing_type = request.form.get("existingType")
    new_type_checkbox = request.form.get("newTypeCheckbox")
    new_type = request.form.get("newTemplateType")
    new_template_name = request.form["newTemplateName"]
    new_template_file = request.files["newTemplateFile"]

    if new_type_checkbox and new_type:
        animation_type = new_type
    else:
        animation_type = existing_type

    # Save the uploaded template file
    if new_template_file and new_template_file.filename.endswith(".json"):
        file_path = os.path.join(UPLOADED_JSON_FILE_FOLDER, new_template_file.filename)
        new_template_file.save(file_path)

        # Update the TEMPLATE_MAPPING
        if animation_type in TEMPLATE_MAPPING:
            TEMPLATE_MAPPING[animation_type][new_template_name] = file_path
        else:
            TEMPLATE_MAPPING[animation_type] = {new_template_name: file_path}

        return redirect(url_for("index"))

    else:
        return "Invalid file type. Please upload a .json file.", 400


if __name__ == "__main__":
    app.run(debug=True)
