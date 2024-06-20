from flask import Flask, request, jsonify, send_file
import os
import subprocess
import pyautogui
import pygetwindow as gw
import ctypes
import time
import datetime

app = Flask(__name__, static_url_path="/static")
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

SPINE_FOLDER_PATH = os.path.join(CURRENT_DIR, "HTML", "spine")
UPLOAD_IMG_FOLDER = os.path.join(CURRENT_DIR, "HTML", "static", "Image", "Saved")
JSON_FILE_FOLDER = os.path.join(CURRENT_DIR, "HTML", "static", "JsonFile")

GIF_BUTTON_IMG_PATH = os.path.join(
    CURRENT_DIR, "HTML", "spine", "Image", "gif_button.png"
)
GIF_BUTTON_IMG_SE_PATH = os.path.join(
    CURRENT_DIR, "HTML", "spine", "Image", "gif_button_selected.png"
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


@app.route("/process", methods=["POST"])
def process():
    data = request.json
    image_file = data["image_path"]
    json_file = data["json_path"]
    output_gif_path = os.path.join(UPLOAD_IMG_FOLDER, "output_gif.gif")

    # save json file to local path
    json_path = os.path.join(JSON_FILE_FOLDER, json_file.filename)
    json_file.save(json_path)

    spine_path = FindSpineProgram()
    # launch Spine CLI to export .spine file from animation.json
    now = datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=8)))
    timeslot = now.strftime("%Y%m%d%H%M%S")  # yyyymmddhhmmss
    output_spine_name = "output" + timeslot + ".spine"
    spine_file_path = os.path.join(SPINE_FOLDER_PATH, output_spine_name)

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
    time.sleep(10)

    retries = 5
    while retries > 0:
        windows = gw.getWindowsWithTitle("Spine - output")
        if windows:
            try:
                spine_window = windows[0]
                spine_window.activate()
                time.sleep(0.5)
                pyautogui.hotkey("ctrl", "e")
                ChangeLanguageEng()
                # pyautogui.click(x=327, y=422)
                time.sleep(1)
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
                time.sleep(1)
                break
            except Exception as e:
                print(f"Failed to activate Spine window: {e}")
                time.sleep(1)
        retries -= 1
        print(f"Retrying... ({5 - retries}/5)")
    if retries == 0:
        return jsonify({"error": "Failed to activate Spine window"}), 500

    return send_file(output_gif_path, mimetype="image/gif")


if __name__ == "__main__":
    app.run(port=5001)
