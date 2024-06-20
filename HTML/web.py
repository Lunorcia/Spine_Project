from flask import Flask, render_template, request, url_for, redirect, jsonify
import pathlib
import sys
import os
import requests

SRC_PATH = pathlib.Path(__file__).parent.absolute()  # (web.py)'s parent path = /HTML
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.path.append(str(SRC_PATH))  # ensure SRC_PATH is in sys.path
PYTHON_FILE_FOLDER = os.path.join(SRC_PATH, "pythonFile")
sys.path.append(str(PYTHON_FILE_FOLDER))
import pythonFile.animate as animate


# src = (absolute path)\HTML
# location of img file which user upload
UPLOAD_IMG_FOLDER = os.path.join(SRC_PATH, "static", "Image", "Saved")
JSON_FILE_FOLDER = os.path.join(SRC_PATH, "static", "JsonFile")
UPLOADED_JSON_FILE_FOLDER = os.path.join(SRC_PATH, "static", "UploadedJson")


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


app = Flask(__name__, static_url_path="/static")


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
    # 將圖片保存到伺服器
    uploaded_image.save(os.path.join(UPLOAD_IMG_FOLDER, uploaded_image.filename))
    img_url = f"/Image/Saved/{uploaded_image.filename}"  # /static written in html
    saved_img_path = os.path.join(UPLOAD_IMG_FOLDER, uploaded_image.filename)

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

    animate.SetImgPath(saved_img_path)
    animate.SetJsonFile(saved_json_path)
    animate.main()

    # send file to local server
    try:
        with open(saved_json_path, "rb") as json_file, open(
            saved_img_path, "rb"
        ) as img_file:
            print("Before send request.\n")
            response = requests.post(
                "http://192.168.56.1:5001/process",
                files={"json_file": json_file, "image_file": img_file},
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
                    templates=TEMPLATE_MAPPING,
                )
            else:
                print("Request error.\n")
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
