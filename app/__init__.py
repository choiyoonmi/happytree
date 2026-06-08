import os
from pathlib import Path

from flask import Flask

from .routes import bp


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-change-me"),
        MAX_CONTENT_LENGTH=20 * 1024 * 1024,
        UPLOAD_FOLDER=Path(app.instance_path) / "uploads",
        JOB_FOLDER=Path(app.instance_path) / "jobs",
        OUTPUT_FOLDER=Path(app.instance_path) / "outputs",
    )
    if test_config:
        app.config.update(test_config)

    for key in ("UPLOAD_FOLDER", "JOB_FOLDER", "OUTPUT_FOLDER"):
        Path(app.config[key]).mkdir(parents=True, exist_ok=True)

    app.register_blueprint(bp)
    return app
