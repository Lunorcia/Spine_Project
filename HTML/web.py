from flask import Flask, render_template, request, url_for, redirect, jsonify, send_file
import pathlib
import sys
import os
import requests
import mimetypes
import json


SRC_PATH = pathlib.Path(__file__).parent.absolute()  # (web.py)'s parent path = /HTML
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.path.append(str(SRC_PATH))  # ensure SRC_PATH is in sys.path
PYTHON_FILE_FOLDER = os.path.join(SRC_PATH, "pythonFile")
sys.path.append(str(PYTHON_FILE_FOLDER))
import pythonFile.animate as animate
import pythonFile.enlarge_mesh as enlargeMesh

LOCAL_SERVER_ADDR = "https://51c6-219-70-173-170.ngrok-free.app/process"

# src = (absolute path)\HTML
# location of img file which user upload
UPLOAD_IMG_FOLDER = os.path.join(SRC_PATH, "static", "Image", "Saved")
JSON_FILE_FOLDER = os.path.join(SRC_PATH, "static", "JsonFile")
UPLOADED_JSON_FILE_FOLDER = os.path.join(SRC_PATH, "static", "UploadedJson")
TEMPLATE_MAPPING_FILE = os.path.join(SRC_PATH, "template_mapping.json")

TEMPLATE_MAPPING = {
    "Only Scale": {
        "Sym_bomp_01": {
            "file": os.path.join(JSON_FILE_FOLDER, "Sym_bomp_01.json"),
        },
        "Sym_bomp_02": {
            "file": os.path.join(JSON_FILE_FOLDER, "Sym_bomp_02.json"),
        },
        "Sym_Tip_01": {
            "file": os.path.join(JSON_FILE_FOLDER, "Sym_Tip_01.json"),
        },
    },
    "Scale & rotate": {
        "01win": {
            "file": os.path.join(JSON_FILE_FOLDER, "01win.json"),
        },
        "Sym_Cascading_01": {
            "file": os.path.join(JSON_FILE_FOLDER, "Sym_Cascading_01.json"),
        },
        "Sym_bomp_03": {
            "file": os.path.join(JSON_FILE_FOLDER, "Sym_bomp_03.json"),
        },
        "Sym_bomp_06": {
            "file": os.path.join(JSON_FILE_FOLDER, "Sym_bomp_06.json"),
        },
        "Sym_bomp_07": {
            "file": os.path.join(JSON_FILE_FOLDER, "Sym_bomp_07.json"),
        },
    },
    "Scale & translate": {
        "Sym_Cascading_02": {
            "file": os.path.join(JSON_FILE_FOLDER, "Sym_Cascading_02.json"),
        },
        "Sym_bomp_04": {
            "file": os.path.join(JSON_FILE_FOLDER, "Sym_bomp_04.json"),
        },
        "Sym_bomp_05": {
            "file": os.path.join(JSON_FILE_FOLDER, "Sym_bomp_05.json"),
        },
    },
}


app = Flask(__name__, static_url_path="/static")


def load_template_mapping():
    if os.path.exists(TEMPLATE_MAPPING_FILE):
        with open(TEMPLATE_MAPPING_FILE, "r") as f:
            return json.load(f)
    return TEMPLATE_MAPPING


def save_template_mapping(mapping):
    with open(TEMPLATE_MAPPING_FILE, "w") as f:
        json.dump(mapping, f, indent=4)


@app.route("/")
def index():
    mapping = load_template_mapping()
    for type, templates in mapping.items():
        for t_name, t_data in templates.items():
            t_data["gifUrl"] = (
                url_for("static", filename=f"Image/PreviewGIF/{t_name}.gif"),
            )
    save_template_mapping(mapping)
    return render_template(
        "anim.html", image_web_url="", gif_web_url="", templates=mapping
    )


@app.route("/add_template_page")
def add_template_page():
    mapping = load_template_mapping()
    return render_template("add_template.html", templates=mapping)


@app.route("/adjust_template_page")
def adjust_template_page():
    return render_template("adjust_template.html")


@app.route("/upload", methods=["POST"])
def upload():
    # 取得表單中的參數值
    uploaded_image = request.files["image"]
    selected_letter = request.form["letter"]
    selected_template = request.form["template"]
    selected_type = request.form["animationType"]
    intensity_translate = float(request.form.get("intensityTranslate", 1.0))
    intensity_scale = float(request.form.get("intensityScale", 1.0))
    intensity_rotate = float(request.form.get("intensityRotate", 1.0))
    speed = float(request.form.get("speed", 1.0))
    # 將圖片保存到伺服器
    uploaded_image.save(os.path.join(UPLOAD_IMG_FOLDER, uploaded_image.filename))
    img_url = f"/Image/Saved/{uploaded_image.filename}"  # /static written in html
    saved_img_path = os.path.join(UPLOAD_IMG_FOLDER, uploaded_image.filename)

    # choose template json
    mapping = load_template_mapping()
    type_dict = mapping.get(selected_type)
    template_data = type_dict.get(selected_template)
    template_json_path = template_data.get("file")
    saved_json_path = ""
    if not template_json_path or not os.path.exists(template_json_path):
        print("template doesn't exist\n")
        json_filename = "animation.json"
        saved_json_path = os.path.join(JSON_FILE_FOLDER, json_filename)
    else:
        print(f"template path: {template_json_path}\n")
        saved_json_path = template_json_path

    animate.SetImgPath(saved_img_path)
    animate.SetJsonFile(saved_json_path)
    animate.main()

    # send file to local server
    try:
        with open(saved_json_path, "rb") as json_file, open(
            saved_img_path, "rb"
        ) as img_file:
            json_filename = os.path.basename(saved_json_path)
            img_filename = os.path.basename(saved_img_path)
            print("Before send request.\n")
            img_mime_type, _ = mimetypes.guess_type(img_filename)
            response = requests.post(
                LOCAL_SERVER_ADDR,
                files={
                    "json_file": (json_filename, json_file, "application/json"),
                    "image_file": (img_filename, img_file, img_mime_type),
                },
                data={
                    "intensityTranslate": intensity_translate,
                    "intensityScale": intensity_scale,
                    "intensityRotate": intensity_rotate,
                    "speed": speed,
                },
                timeout=180,
            )

            if response.status_code == 200:
                # save gif file to the folder
                output_gif_path = os.path.join(UPLOAD_IMG_FOLDER, "output_gif.gif")
                with open(output_gif_path, "wb") as gif_file:
                    gif_file.write(response.content)
                gif_url = f"/Image/Saved/output_gif.gif"  # /static written in html
                return render_template(
                    "anim.html",
                    image_web_url=img_url,
                    gif_web_url=gif_url,
                    templates=mapping,
                )
            else:
                print("Request failed.\n")
                return jsonify({"error": "Failed to process image"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/add_template", methods=["POST"])
def add_template():
    existing_type = request.form.get("existingType")
    new_type_checkbox = request.form.get("newTypeCheckbox")
    new_type = request.form.get("newTemplateType")
    new_template_name = request.form["newTemplateName"]
    new_template_file = request.files["newTemplateFile"]
    # new_template_preview

    if new_type_checkbox and new_type:
        animation_type = new_type
    else:
        animation_type = existing_type

    # Save the uploaded template file
    if new_template_file and new_template_file.filename.endswith(".json"):
        file_path = os.path.join(UPLOADED_JSON_FILE_FOLDER, new_template_file.filename)
        new_template_file.save(file_path)

        # generate preview gif
        preview_file_name = f"{new_template_name}.gif"
        preview_file_path = os.path.join(
            SRC_PATH, "static", "Image", "PreviewGIF", preview_file_name
        )
        # connect local server
        generate_preview_gif(file_path, preview_file_path)

        # Update the TEMPLATE_MAPPING
        mapping = load_template_mapping()
        new_template_data = {
            "file": file_path,
            "gifUrl": url_for(
                "static", filename=f"Image/PreviewGIF/{preview_file_name}"
            ),
        }
        if animation_type in mapping:
            mapping[animation_type][new_template_name] = new_template_data
        else:
            mapping[animation_type] = {new_template_name: new_template_data}

        save_template_mapping(mapping)

        return redirect(url_for("index"))

    else:
        return "Invalid file type. Please upload a .json file.", 400


def generate_preview_gif(json_file_path, preview_gif_path):
    preview_img = "preview_base.png"
    preview_img_path = os.path.join(SRC_PATH, "static", "Image", preview_img)

    animate.SetImgPath(preview_img_path)
    animate.SetJsonFile(json_file_path)
    animate.main()

    # send file to local server
    try:
        with open(json_file_path, "rb") as json_file, open(
            preview_img_path, "rb"
        ) as img_file:
            json_filename = os.path.basename(json_file_path)
            img_filename = os.path.basename(preview_img_path)
            print("Before send request.\n")
            img_mime_type, _ = mimetypes.guess_type(img_filename)
            response = requests.post(
                LOCAL_SERVER_ADDR,
                files={
                    "json_file": (json_filename, json_file, "application/json"),
                    "image_file": (img_filename, img_file, img_mime_type),
                },
                data={
                    "intensityTranslate": 1.0,
                    "intensityScale": 1.0,
                    "intensityRotate": 1.0,
                    "speed": 1.0,
                },
                timeout=180,
            )

            if response.status_code == 200:
                # save gif file to the folder
                output_gif_path = preview_gif_path
                with open(output_gif_path, "wb") as gif_file:
                    gif_file.write(response.content)
                return
            else:
                print("Request failed.\n")
                return jsonify({"error": "Failed to process image"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # animate.py改圖片路徑(用As.png)
    # 連線local server，傳模板json檔案和As.png給server
    # server call spine，回傳gif
    # 把gif存到static的PreviewGIF裡，檔名命名{preview_file_name}


@app.route("/adjust_template", methods=["POST"])
def adjust_template():
    # 取得表單上傳的文件
    uploaded_image = request.files["image_file"]
    uploaded_json = request.files["json_file"]
    scale_factor = float(request.form.get("scale_factor", 2.0))
    if not uploaded_image or not uploaded_image:
        return "Please upload both JSON and image files then try again.", 400

    # 將檔案儲存到伺服器
    saved_img_path = os.path.join(UPLOAD_IMG_FOLDER, uploaded_image.filename)
    saved_json_path = os.path.join(UPLOADED_JSON_FILE_FOLDER, uploaded_json.filename)
    uploaded_image.save(saved_img_path)
    uploaded_json.save(saved_json_path)

    enlargeMesh.SetImgPath(saved_img_path)
    enlargeMesh.SetJsonPath(saved_json_path)
    enlargeMesh.SetScale(scale_factor)
    modified_json_file, modified_img_file = enlargeMesh.main()

    json_download_url = url_for(
        "download_file", folder="json", filename=os.path.basename(modified_json_file)
    )
    img_download_url = url_for(
        "download_file", folder="img", filename=os.path.basename(modified_img_file)
    )
    return render_template(
        "adjust_template.html",
        json_download_link=json_download_url,
        img_download_link=img_download_url,
    )

    # code todo:
    # 存檔新json
    # 回傳json檔案在網頁讓使用者下載或選擇繼續轉成gif輸出

    # 讓使用者下載放大邊緣後的圖片
    # 產出json回傳，要一起產出GIF

    # todo: 動畫AKQJ列表


@app.route("/download/<folder>/<filename>")
def download_file(folder, filename):
    if folder == "json":
        file_path = os.path.join(UPLOADED_JSON_FILE_FOLDER, filename)
    elif folder == "img":
        file_path = os.path.join(UPLOAD_IMG_FOLDER, filename)
    else:
        return "Invalid folder", 400
    return send_file(file_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
