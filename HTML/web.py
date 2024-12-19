import zipfile
from flask import (
    Flask,
    render_template,
    request,
    url_for,
    redirect,
    jsonify,
    send_file,
)
import pathlib
import sys
import os
import requests
import mimetypes
import json
import shutil
import threading
from threading import Lock

app = Flask(__name__, static_url_path="/static")

SRC_PATH = pathlib.Path(__file__).parent.absolute()  # (web.py)'s parent path = /HTML
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.path.append(str(SRC_PATH))  # ensure SRC_PATH is in sys.path
PYTHON_FILE_FOLDER = os.path.join(SRC_PATH, "pythonFile")
sys.path.append(str(PYTHON_FILE_FOLDER))
import pythonFile.animate as animate
import pythonFile.enlarge_mesh as enlargeMesh

LOCAL_SERVER_MAIN = "https://ced0-219-70-173-170.ngrok-free.app/main_process"
LOCAL_SERVER_MESH = "https://ced0-219-70-173-170.ngrok-free.app/mesh_process"
LOCAL_SERVER_MAPPING = "https://ced0-219-70-173-170.ngrok-free.app/mapping_process"
LOCAL_SERVER_GAME = "https://ced0-219-70-173-170.ngrok-free.app/game_url_process"

# src = (absolute path)\HTML
# location of img file which user upload
UPLOAD_IMG_FOLDER = os.path.join(SRC_PATH, "static", "Image", "Saved")
JSON_FILE_FOLDER = os.path.join(SRC_PATH, "static", "JsonFile")
UPLOADED_JSON_FILE_FOLDER = os.path.join(SRC_PATH, "static", "UploadedJson")
UNZIP_FOLDER = os.path.join(SRC_PATH, "static", "UnzipFromWeb")
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


def load_template_mapping():
    if os.path.exists(TEMPLATE_MAPPING_FILE):
        with open(TEMPLATE_MAPPING_FILE, "r") as f:
            return json.load(f)
    print("No default mapping, return empty list")
    return {}


def save_template_mapping(mapping):
    # save json on web server
    with open(TEMPLATE_MAPPING_FILE, "w") as f:
        json.dump(mapping, f, indent=4)
    # save json to local server
    try:
        with open(TEMPLATE_MAPPING_FILE, "rb") as json_file:
            print("Before send request(save template mapping).\n")
            response = requests.post(
                LOCAL_SERVER_MAPPING,
                files={"json_file": json_file},
                timeout=180,
            )

            if response.status_code == 200:
                print("Mappings saved to local successfully")
            else:
                print("Request failed.\n")

                return jsonify({"Error": "Saving mappings failed."}), 500
    except Exception as e:
        return jsonify({"Error sending json file to local server": str(e)}), 500


@app.route("/")
def index():
    mapping = load_template_mapping()
    # for type, templates in mapping.items():
    #     for t_name, t_data in templates.items():
    #         t_data["gifUrl"] = url_for(
    #             "static", filename=f"Image/PreviewGIF/{t_name}.gif"
    #         )
    return render_template(
        "anim.html", image_web_url="", gif_web_url="", templates=mapping
    )


@app.route("/add_template_page", methods=["GET", "POST"])
def add_template_page():
    mapping = load_template_mapping()
    # if adjust_template_page send json file path, return file to add_template_page
    new_json_template = request.args.get("json_path")
    gif_file_path = request.args.get("gif_path", "")
    return render_template(
        "add_template.html",
        templates=mapping,
        json_path=new_json_template,
        gif_path=gif_file_path,
    )


@app.route("/adjust_template_page")
def adjust_template_page():
    mapping = load_template_mapping()
    return render_template("adjust_template.html", templates=mapping)


@app.route("/enter_game_url")
def enter_game_url():
    return render_template("fetch_game.html")


processing_status = {"status": "processing", "files": []}
status_lock = threading.Lock()


def local_fetch_process(game_url):
    global processing_status
    processing_status = {"status": "processing", "files": []}
    with app.app_context():
        # send url to local server
        try:
            print("Before send request.\n")
            response = requests.post(
                LOCAL_SERVER_GAME,
                data={
                    "game_url": game_url,
                },
                timeout=180,
                stream=True,
            )

            if response.status_code == 200:
                # get zip file
                if not os.path.exists(UNZIP_FOLDER):
                    print("Create unzip folder.\n")
                    os.makedirs(UNZIP_FOLDER)
                zip_file = os.path.join(UNZIP_FOLDER, "resources.zip")
                with open(zip_file, "wb") as z:
                    z.write(response.content)
                # unzip to UNZIP_FOLDER
                if os.path.exists(zip_file):
                    with zipfile.ZipFile(zip_file, "r") as z:
                        z.extractall(UNZIP_FOLDER)
                        print("Extract zip complete.\n")
                else:
                    print("Cannot find zip file at web.\n")
                with status_lock:
                    print("Status change to complete.(in local_fetch_process)\n")
                    processing_status = {
                        "status": "completed",
                        "files": [],
                    }  # let check_processing_status() to fill files url list

            else:
                with status_lock:
                    print("Request failed. (in web.py local_fetch_process())\n")
                    processing_status = {
                        "status": "error",
                        "message": "local_server return error",
                    }
        except Exception as e:
            with status_lock:
                print(f"fetch game url error: {str(e)}")
                processing_status = {"status": "error", "message": str(e)}


@app.route("/fetch_game_resources", methods=["POST"])
def fetch_game_resources():
    global processing_status
    game_url = request.form["game_url"]
    with status_lock:
        processing_status = {"status": "processing", "files": []}  # init
    print(f"Fetch start, init status: {processing_status["status"]}\n")
    # before write zip file, clear folder
    if os.path.exists(UNZIP_FOLDER):
        for file_name in os.listdir(UNZIP_FOLDER):
            file_path = os.path.join(UNZIP_FOLDER, file_name)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # 移除檔案或符號連結
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # 移除目錄及其內部內容
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
    local_thread = threading.Thread(target=local_fetch_process, args=(game_url,))

    local_thread.start()

    return jsonify({"status": "processing"}), 202


@app.route("/check_processing_status", methods=["GET"])
def check_processing_status():
    global processing_status
    with status_lock:
        if processing_status["status"] == "completed":
            print("Checking status completed.\n")
            files_list = os.listdir(UNZIP_FOLDER)
            if len(files_list) > 0:
                file_urls = []
                for file_name in files_list:
                    file_url = url_for(
                        "download_file", folder="zip", filename=file_name
                    )
                    file_path = os.path.join(UNZIP_FOLDER, file_name)
                    file_urls.append(
                        {
                            "file_name": file_name,
                            "file_url": file_url,
                            "file_path": file_path,
                        }
                    )

                # sorting seq: zip -> json -> png -> atlas
                def file_sort_key(file_info):
                    if file_info["file_name"].endswith(".zip"):
                        return 0
                    elif file_info["file_name"].endswith(".json"):
                        return 1
                    elif file_info["file_name"].endswith(".png"):
                        return 2
                    elif file_info["file_name"].endswith(".atlas"):
                        return 3
                    return 4

                file_urls.sort(key=file_sort_key)

                print("Status change to complete.(in check_processing_status)\n")
                processing_status = {"status": "completed", "files": file_urls}
                print("extract files complete. (in web.py local_fetch_process())\n")
                return jsonify(processing_status)
        elif processing_status["status"] == "error":
            return jsonify(processing_status)
        processing_status = {"status": "processing", "files": []}
        return jsonify(processing_status)


@app.route("/download_mapping")
def download_mapping():
    if os.path.exists(TEMPLATE_MAPPING_FILE):
        return send_file(
            TEMPLATE_MAPPING_FILE,
            as_attachment=True,
            download_name="template_mapping.json",
        )


@app.route("/download_all_templates")
def download_all_templates():
    temp_dir = os.path.join(SRC_PATH, "static", "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    mapping = load_template_mapping()
    for template_type, templates in mapping.items():
        for template_name, template_info in templates.items():
            json_file_path = template_info.get("file")
            gif_file_path = template_info.get("gifUrl")
            # gif_file_path is list
            if isinstance(gif_file_path, list) and gif_file_path:
                gif_file_path = gif_file_path[0]  # only one path in this list
            gif_full_path = os.path.join(
                SRC_PATH, gif_file_path.lstrip("/")
            )  # turn into abs path

            if os.path.exists(json_file_path):
                shutil.copy(json_file_path, temp_dir)
            if os.path.exists(gif_full_path):
                shutil.copy(gif_full_path, temp_dir)
    zip_filename = "mapping_file.zip"
    zip_path = os.path.join(SRC_PATH, "static", zip_filename)
    shutil.make_archive(zip_path.replace(".zip", ""), "zip", temp_dir)
    shutil.rmtree(temp_dir)  # clear dir
    return send_file(zip_path, as_attachment=True)


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
    saved_json_path = animate.main()

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
                LOCAL_SERVER_MAIN,
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
                return render_template(
                    "anim.html",
                    error_message="Failed to process animation in Spine2D.",
                    image_web_url=img_url,
                    templates=mapping,
                )
                # return jsonify({"error": "Failed to process image"}), 500
    except Exception as e:
        return render_template(
            "anim.html",
            error_message=f"Local server transmission error: {str(e)}",
            image_web_url=img_url,
            templates=mapping,
        )
        # return jsonify({"error": str(e)}), 500


@app.route("/add_template", methods=["POST"])
def add_template():
    existing_type = request.form.get("existingType")
    new_type_checkbox = request.form.get("newTypeCheckbox")
    new_type = request.form.get("newTemplateType")
    new_template_name = request.form["newTemplateName"]
    new_template_file = request.files.get("newTemplateFile")
    new_template_gif = request.files.get("newTemplateGif")
    json_file_path = request.form.get("jsonFilePath")
    gif_file_path = request.form.get("gifFilePath")

    if json_file_path and gif_file_path:
        # if web send json file's path and gif file, then do not generate gif
        return save_json_template(
            existing_type,
            new_type_checkbox,
            new_type,
            new_template_name,
            json_file_path,
            gif_file_path,
        )

    # new_template_preview
    if new_type_checkbox and new_type:
        animation_type = new_type
    else:
        animation_type = existing_type

    # Save the uploaded template file
    if new_template_file and new_template_file.filename.endswith(".json"):
        file_path = os.path.join(UPLOADED_JSON_FILE_FOLDER, new_template_file.filename)
        new_template_file.save(file_path)

        if new_template_gif:  # doesn't need to generate gif
            # save gif file to server
            gif_file_path = os.path.join(UPLOAD_IMG_FOLDER, new_template_gif.filename)
            new_template_gif.save(gif_file_path)
            return save_json_template(
                existing_type,
                new_type_checkbox,
                new_type,
                new_template_name,
                file_path,
                gif_file_path,
            )

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

    # only json_path (send from fetch_game page)
    elif json_file_path:
        print(f"json_file_path at: {json_file_path}\n")
        if not os.path.exists(json_file_path):
            print("Json path error.\n")
            return "Json file path doesn't exist.", 400
        if not json_file_path.endswith(".json"):
            print("Json end format error.\n")
            return "Invalid file type. Please upload a .json file.", 400

        # Save the uploaded template file
        if not os.path.exists(UPLOADED_JSON_FILE_FOLDER):
            os.makedirs(UPLOADED_JSON_FILE_FOLDER)
        file_path = os.path.join(
            UPLOADED_JSON_FILE_FOLDER, os.path.basename(json_file_path)
        )
        shutil.copy(json_file_path, file_path)

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


# if doesn't need to generate gif, call this function
def save_json_template(
    existing_type,
    new_type_checkbox,
    new_type,
    new_template_name,
    json_file_path,
    gif_file_path,
):
    if new_type_checkbox and new_type:
        animation_type = new_type
    else:
        animation_type = existing_type

    json_file_path = os.path.abspath(json_file_path)
    gif_file_path = os.path.abspath(gif_file_path)

    # json has been in UPLOADED_JSON_FILE_FOLDER
    # save preview gif
    preview_file_name = f"{new_template_name}.gif"
    preview_file_path = os.path.join(
        SRC_PATH, "static", "Image", "PreviewGIF", preview_file_name
    )
    gif_file_path = os.path.normpath(gif_file_path)
    if os.path.exists(gif_file_path):
        # copy gif from gif_path to preview_path
        print(f"copying gif from {gif_file_path} to {preview_file_path}")
        shutil.copy(gif_file_path, preview_file_path)
    else:
        print("gif file path doesn't exist.")

    # Update the TEMPLATE_MAPPING
    mapping = load_template_mapping()
    new_template_data = {
        "file": json_file_path,
        "gifUrl": url_for("static", filename=f"Image/PreviewGIF/{preview_file_name}"),
    }
    if animation_type in mapping:
        mapping[animation_type][new_template_name] = new_template_data
    else:
        mapping[animation_type] = {new_template_name: new_template_data}

    save_template_mapping(mapping)

    return redirect(url_for("index"))


def generate_preview_gif(json_file_path, preview_gif_path):
    preview_img = "preview_base.png"
    preview_img_path = os.path.join(SRC_PATH, "static", "Image", preview_img)

    animate.SetImgPath(preview_img_path)
    animate.SetJsonFile(json_file_path)
    json_file_path = animate.main()

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
                LOCAL_SERVER_MAIN,
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
    mapping = load_template_mapping()
    # 取得表單上傳的文件
    uploaded_image = request.files["image_file"]
    scale_factor = float(request.form.get("scale_factor", 2.0))

    if not uploaded_image or not uploaded_image:
        return "Please upload both JSON and image files then try again.", 400

    # 選擇既有模板或使用者自行上傳模板
    use_existing_template = request.form.get("existingTemplateCheckbox") == "on"
    saved_json_path = ""
    if use_existing_template:
        uploaded_json = request.files.get("json_file")
        # 將模板檔案儲存到伺服器
        saved_json_path = os.path.join(
            UPLOADED_JSON_FILE_FOLDER, uploaded_json.filename
        )
        uploaded_json.save(saved_json_path)

    else:
        selected_type = request.form.get("animationType", "")
        selected_template = request.form.get("template", "")
        # choose template json
        type_dict = mapping.get(selected_type)
        template_data = type_dict.get(selected_template)
        template_json_path = template_data.get("file")
        if not template_json_path or not os.path.exists(template_json_path):
            print("template doesn't exist\n")
            json_filename = "animation.json"
            template_json_path = os.path.join(JSON_FILE_FOLDER, json_filename)
        else:
            print(f"template path: {template_json_path}\n")
        # 將模板檔案儲存到伺服器
        saved_json_path = os.path.join(
            UPLOADED_JSON_FILE_FOLDER, os.path.basename(template_json_path)
        )
        shutil.copy(template_json_path, saved_json_path)

    # 將圖片檔案儲存到伺服器
    saved_img_path = os.path.join(UPLOAD_IMG_FOLDER, uploaded_image.filename)
    uploaded_image.save(saved_img_path)

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

    # send file to local server
    try:
        with open(modified_json_file, "rb") as json_file, open(
            modified_img_file, "rb"
        ) as img_file:
            json_filename = os.path.basename(modified_json_file)
            img_filename = os.path.basename(modified_img_file)
            print("Before send request.\n")
            img_mime_type, _ = mimetypes.guess_type(img_filename)
            response = requests.post(
                LOCAL_SERVER_MESH,
                files={
                    "json_file": (json_filename, json_file, "application/json"),
                    "image_file": (img_filename, img_file, img_mime_type),
                },
                timeout=180,
            )

            if response.status_code == 200:
                # save gif file to the folder
                output_gif_path = os.path.join(UPLOAD_IMG_FOLDER, "output_gif.gif")
                with open(output_gif_path, "wb") as gif_file:
                    gif_file.write(response.content)

                gif_url = url_for("static", filename="/Image/Saved/output_gif.gif")
                return render_template(
                    "adjust_template.html",
                    gif_web_url=gif_url,
                    json_download_link=json_download_url,
                    img_download_link=img_download_url,
                    json_file_path=modified_json_file,
                    gif_file_path=output_gif_path,
                    templates=mapping,
                )
            else:
                print("Request failed.\n")
                return jsonify({"error": "Failed to process image"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download/<folder>/<filename>")
def download_file(folder, filename):
    if folder == "json":
        file_path = os.path.join(UPLOADED_JSON_FILE_FOLDER, filename)
    elif folder == "img":
        file_path = os.path.join(UPLOAD_IMG_FOLDER, filename)
    elif folder == "zip":
        file_path = os.path.join(UNZIP_FOLDER, filename)
    else:
        return "Invalid folder", 400
    return send_file(file_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
