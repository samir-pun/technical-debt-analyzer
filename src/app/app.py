"""
app.py

Flask web dashboard for the Technical Debt Analyzer.

Run from the project root with:
    python3 -m src.app.app
Then open http://127.0.0.1:5001
"""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

from flask import Flask, Response, render_template, request
from plotly.offline import get_plotlyjs
from werkzeug.utils import secure_filename

from ..pipeline import predict_project
from .charts import build_charts

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB upload limit

ALLOWED_SUFFIXES = {".py", ".zip"}
_PLOTLY_JS = None


@app.errorhandler(413)
def too_large(_error):
    return render_template(
        "index.html",
        error="That upload is too large (limit 500 MB). Re-zip the project "
              "without venv/, .git/ or node_modules/ folders.",
    ), 413


@app.route("/plotly.js")
def plotly_js():
    """Serve plotly.js from the installed package so charts work offline."""
    global _PLOTLY_JS
    if _PLOTLY_JS is None:
        _PLOTLY_JS = get_plotlyjs()
    return Response(
        _PLOTLY_JS,
        mimetype="application/javascript",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    uploaded = request.files.get("project")
    if uploaded is None or uploaded.filename == "":
        return render_template("index.html", error="Please choose a file to upload."), 400

    filename = secure_filename(uploaded.filename)
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        return render_template("index.html", error="Only .py and .zip files are supported."), 400

    with tempfile.TemporaryDirectory(prefix="tda_upload_") as tmp:
        saved_path = Path(tmp) / filename
        uploaded.save(saved_path)
        try:
            result = predict_project(saved_path)
        except zipfile.BadZipFile:
            return render_template("index.html", error="That file is not a valid .zip archive."), 400
        except (ValueError, FileNotFoundError) as exc:
            return render_template("index.html", error=str(exc)), 400

    try:
        charts = build_charts(result)
    except Exception:
        # Charts are optional: log the problem, but still show the results.
        app.logger.exception("Chart generation failed")
        charts = {}

    return render_template("results.html", result=result, charts=charts)


if __name__ == "__main__":
    # Port 5001, because macOS uses port 5000 for AirPlay Receiver.
    # debug=True is for local development only.
    app.run(host="127.0.0.1", port=5001, debug=True)