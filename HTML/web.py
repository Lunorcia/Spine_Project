from flask import Flask, render_template, request, url_for
import pathlib
import sys
import os
import subprocess
import time
import pyautogui
import pygetwindow as gw
import ctypes

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pythonFile.mesh as mesh
import pythonFile.animate as animate

SRC_PATH = pathlib.Path(__file__).parent.absolute()  # (web.py)'s parent path = /HTML
# src = -absolute path-\HTML
# location of img file which user upload
UPLOAD_IMG_FOLDER = os.path.join(SRC_PATH, "static", "Image", "Saved")
GIF_BUTTON_IMG_PATH = (
    "C:\\Users\\cyivs\\OneDrive\\Desktop\\VSCode\\HTML\\static\\Image\\gif_button.png"
)
GIF_BUTTON_IMG_SE_PATH = "C:\\Users\\cyivs\\OneDrive\\Desktop\\VSCode\\HTML\\static\\Image\\gif_button_selected.png"
JSON_FILE_FOLDER = os.path.join(SRC_PATH, "static", "JsonFile")
SPINE_PROGRAM = "Spine.com"
SPINE_EXE = "Spine.exe"

TEMPLATE_MAPPING = {
    "Sym_bomp_01": os.path.join(JSON_FILE_FOLDER, "Sym_bomp_01.json"),
    "Sym_bomp_02": os.path.join(JSON_FILE_FOLDER, "Sym_bomp_02.json"),
    "Sym_bomp_03": os.path.join(JSON_FILE_FOLDER, "Sym_bomp_03.json"),
    "Sym_bomp_04": os.path.join(JSON_FILE_FOLDER, "Sym_bomp_04.json"),
    "Sym_bomp_05": os.path.join(JSON_FILE_FOLDER, "Sym_bomp_05.json"),
    "Sym_bomp_06": os.path.join(JSON_FILE_FOLDER, "Sym_bomp_06.json"),
    "Sym_bomp_07": os.path.join(JSON_FILE_FOLDER, "Sym_bomp_07.json"),
    "Sym_Cascading_01": os.path.join(JSON_FILE_FOLDER, "Sym_Cascading_01.json"),
    "Sym_Cascading_02": os.path.join(JSON_FILE_FOLDER, "Sym_Cascading_02.json"),
    "Sym_Tip_01": os.path.join(JSON_FILE_FOLDER, "Sym_Tip_01.json"),
    "Sym_Tip_02": os.path.join(JSON_FILE_FOLDER, "Sym_Tip_02.json"),
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
    return render_template("anim.html", image_url="/Image/Qe.png")


@app.route("/upload", methods=["POST"])
def upload():
    # 取得表單中的參數值
    uploaded_image = request.files["image"]
    selected_letter = request.form["letter"]
    selected_template = request.form["template"]
    # 進行進一步的處理，例如將圖片保存到伺服器或進行其他操作
    if request.method == "POST":
        uploaded_image.save(os.path.join(UPLOAD_IMG_FOLDER, uploaded_image.filename))
        img_url = f"/Image/Saved/{uploaded_image.filename}"  # /static written in html
        saved_img_path = os.path.join(UPLOAD_IMG_FOLDER, uploaded_image.filename)

        # generate json file
        # mesh.SetImgPath(saved_img_path)
        # mesh.main()
        animate.SetImgPath(saved_img_path)
        animate.main()
        # choose template json
        template_json_path = TEMPLATE_MAPPING.get(selected_template)
        if not template_json_path or not os.path.exists(template_json_path):
            print("template doesn't exist\n")
            json_filename = "animation.json"
            saved_json_path = os.path.join(JSON_FILE_FOLDER, json_filename)
        else:
            print(f"template path: {template_json_path}\n")
            saved_json_path = template_json_path

            # launch Spine from cmd
            spine_path = FindSpineProgram()
            if spine_path:
                print(f"spine path = {spine_path}")
                try:
                    # launch Spine CLI to export .spine file from animation.json
                    spine_file_path = "E:/testSpine/output.spine"
                    subprocess.run(
                        [
                            spine_path,
                            "-i",
                            saved_json_path,
                            "-o",
                            spine_file_path,
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

                    retries = 10
                    while retries > 0:
                        windows = gw.getWindowsWithTitle("Spine - output")
                        if windows:
                            try:
                                spine_window = windows[0]
                                spine_window.activate()
                                time.sleep(0.5)
                                spine_window.maximize()
                                time.sleep(0.5)
                                pyautogui.hotkey("ctrl", "e")
                                ChangeLanguageEng()
                                pyautogui.click(x=327, y=422)
                                time.sleep(1)
                                # click GIF button
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
                                        time.sleep(1)
                                        pyautogui.click(gif_button_location)
                                        time.sleep(0.5)
                                    else:
                                        print("Try to find GIF radio button.")
                                        gif_button_location = pyautogui.locateOnScreen(
                                            GIF_BUTTON_IMG_SE_PATH
                                        )
                                        if gif_button_location is not None:
                                            print(" GIF radio button_SE found.")
                                            gif_button_location = pyautogui.center(
                                                gif_button_location
                                            )
                                            time.sleep(1)
                                            pyautogui.click(gif_button_location)
                                            time.sleep(0.5)
                                            pyautogui.click(gif_button_location)

                                        else:
                                            print(
                                                "Alternate GIF radio button not found."
                                            )
                                            raise Exception(
                                                "GIF radio button not found"
                                            )
                                except Exception as e:
                                    print(f"Failed to find GIF button: {e}")
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
                        print(f"Retrying... ({10 - retries}/10)")
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
                    "anim.html", image_web_url=img_url, gif_web_url=gif_url
                )
            # print("/upload/post")
            else:
                print("return img only")
                return render_template("anim.html", image_web_url=img_url)

    else:
        print("/upload/other")
        return render_template("anim.html")


if __name__ == "__main__":
    app.run(debug=True)
