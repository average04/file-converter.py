import os
import uuid
import webview
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify
from app.services.converter import pdf_to_docx, docx_to_pdf
from app import get_window, get_output_dir, set_output_dir

bp = Blueprint("converter", __name__)

UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


@bp.get("/")
def index():
    return render_template("index.html", output_dir=str(get_output_dir()))


@bp.get("/api/output-dir")
def api_get_output_dir():
    return jsonify({"path": str(get_output_dir())})


@bp.post("/pick-folder")
def pick_folder():
    window = get_window()
    if window is None:
        return jsonify({"path": None})
    result = window.create_file_dialog(webview.FOLDER_DIALOG)
    if result:
        set_output_dir(result[0])
        return jsonify({"path": result[0]})
    return jsonify({"path": None})


@bp.post("/convert")
def convert():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    mode = request.form.get("mode", "")

    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    suffix = Path(file.filename).suffix.lower()
    uid = uuid.uuid4().hex
    stem = Path(file.filename).stem

    output_dir = get_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    if mode == "pdf_to_docx":
        if suffix != ".pdf":
            return jsonify({"error": "Please upload a PDF file"}), 400
        input_path  = UPLOAD_DIR / f"{uid}.pdf"
        output_path = output_dir / f"{stem}.docx"
        file.save(input_path)
        try:
            pdf_to_docx(input_path, output_path)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif mode == "docx_to_pdf":
        if suffix not in (".docx", ".doc"):
            return jsonify({"error": "Please upload a Word file (.docx or .doc)"}), 400
        input_path  = UPLOAD_DIR / f"{uid}{suffix}"
        output_path = output_dir / f"{stem}.pdf"
        file.save(input_path)
        try:
            docx_to_pdf(input_path, output_path)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    else:
        return jsonify({"error": "Invalid conversion mode"}), 400

    return jsonify({"path": str(output_path), "folder": str(output_dir)})


@bp.post("/open-folder")
def open_folder():
    os.startfile(str(get_output_dir()))
    return jsonify({"ok": True})
