import json
from pathlib import Path

from flask import current_app


def job_path(job_id):
    return Path(current_app.config["JOB_FOLDER"]) / f"{job_id}.json"


def save_job(job):
    path = job_path(job["id"])
    path.write_text(
        json.dumps(job, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_job(job_id):
    path = job_path(job_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

