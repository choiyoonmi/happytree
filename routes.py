from datetime import datetime
import os
from pathlib import Path
import socket
from uuid import uuid4

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from werkzeug.utils import secure_filename

from .services.docx_service import build_exam_docx
from .services.pdf_service import extract_pdf
from .services.question_generator import generate_exam
from .storage import load_job, save_job


bp = Blueprint("main", __name__)
BRAND_LOGO_PATH = Path(
    Path(__file__).parent / "static" / "images" / "happytree-logo.png"
)

@bp.get("/")
def index():
    access_url = mobile_access_url()
    return render_template(
        "index.html",
        mobile_url=access_url,
        public_access=bool(access_url and access_url.startswith("https://")),
    )


@bp.get("/brand-logo.png")
def brand_logo():
    if not BRAND_LOGO_PATH.exists():
        abort(404)
    return send_file(BRAND_LOGO_PATH, mimetype="image/png", max_age=0)


@bp.post("/upload")
def upload():
    pdf = request.files.get("pdf")
    if not pdf or not pdf.filename:
        flash("PDF 파일을 선택해 주세요.", "error")
        return redirect(url_for("main.index"))
    if Path(pdf.filename).suffix.lower() != ".pdf":
        flash("PDF 파일만 업로드할 수 있습니다.", "error")
        return redirect(url_for("main.index"))

    job_id = uuid4().hex[:12]
    safe_name = secure_filename(pdf.filename) or f"{job_id}.pdf"
    upload_path = Path(current_app.config["UPLOAD_FOLDER"]) / f"{job_id}-{safe_name}"
    pdf.save(upload_path)

    try:
        extracted = extract_pdf(upload_path)
    except Exception as exc:
        upload_path.unlink(missing_ok=True)
        flash(f"PDF에서 텍스트를 추출하지 못했습니다: {exc}", "error")
        return redirect(url_for("main.index"))

    job = {
        "id": job_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "filename": pdf.filename,
        "upload_path": str(upload_path),
        "page_count": extracted["page_count"],
        "passages": extracted["passages"],
        "exam": None,
        "student_docx": None,
        "teacher_docx": None,
    }
    save_job(job)
    return redirect(url_for("main.workspace", job_id=job_id))


@bp.get("/workspace/<job_id>")
def workspace(job_id):
    job = require_job(job_id)
    return render_template("workspace.html", job=job)


@bp.get("/workspace/<job_id>/print")
def print_workbook(job_id):
    job = require_job(job_id)
    if not job.get("exam"):
        flash("먼저 문제지를 생성해 주세요.", "error")
        return redirect(url_for("main.workspace", job_id=job_id))
    return render_template("print_workbook.html", job=job, exam=job["exam"])


@bp.post("/workspace/<job_id>/generate")
def generate(job_id):
    job = require_job(job_id)
    selected_ids = set(request.form.getlist("selected"))
    edited_passages = []

    for passage in job["passages"]:
        field = f"text_{passage['id']}"
        if field in request.form:
            passage["text"] = request.form[field].strip()
        passage["selected"] = passage["id"] in selected_ids
        if passage["selected"] and passage["text"]:
            edited_passages.append(passage["text"])

    parts = request.form.getlist("parts")
    if not edited_passages:
        flash("한 개 이상의 지문을 선택해 주세요.", "error")
        save_job(job)
        return redirect(url_for("main.workspace", job_id=job_id))
    if not parts:
        flash("한 개 이상의 PART를 선택해 주세요.", "error")
        save_job(job)
        return redirect(url_for("main.workspace", job_id=job_id))

    requested_count = request.form.get("question_count", "auto")
    answer_mode = request.form.get("answer_mode", "hidden")
    if answer_mode not in {"hidden", "inline", "appendix"}:
        abort(400)
    total_questions = None
    if requested_count != "auto":
        try:
            total_questions = int(requested_count)
        except ValueError:
            abort(400)
        if total_questions not in {200, 500, 700, 1000}:
            abort(400)

    exam = generate_exam(
        edited_passages,
        parts,
        total_questions=total_questions,
    )
    output_dir = Path(current_app.config["OUTPUT_FOLDER"]) / job_id
    student_path = output_dir / "학생용_변형문제.docx"
    teacher_path = output_dir / "교사용_정답해설.docx"
    build_exam_docx(exam, student_path, teacher=False)
    build_exam_docx(exam, teacher_path, teacher=True)

    job["exam"] = exam
    job["question_count"] = requested_count
    job["answer_mode"] = answer_mode
    job["student_docx"] = str(student_path)
    job["teacher_docx"] = str(teacher_path)
    save_job(job)
    flash("문제지와 정답·해설지를 생성했습니다.", "success")
    return redirect(url_for("main.workspace", job_id=job_id))


@bp.get("/download/<job_id>/<kind>")
def download(job_id, kind):
    job = require_job(job_id)
    key = "student_docx" if kind == "student" else "teacher_docx"
    path = job.get(key)
    if not path or not Path(path).exists():
        abort(404)
    return send_file(path, as_attachment=True, download_name=Path(path).name)


def require_job(job_id):
    job = load_job(job_id)
    if not job:
        abort(404)
    return job


def mobile_access_url():
    public_url = os.environ.get("PUBLIC_URL", "").strip().rstrip("/")
    if public_url:
        return public_url
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
            connection.connect(("8.8.8.8", 80))
            address = connection.getsockname()[0]
    except OSError:
        return None
    return f"http://{address}:5000"
