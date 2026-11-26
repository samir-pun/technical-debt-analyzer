"""Checks that the dashboard's CSS and JavaScript live in static files, not in the templates."""

import io
from pathlib import Path

import pytest

from src.app.app import app

SAMPLE = Path(__file__).resolve().parents[1] / "sample_projects" / "low_risk" / "calculator.py"


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def results_page(client):
    return client.post(
        "/analyze",
        data={"project": (io.BytesIO(SAMPLE.read_bytes()), "calculator.py")},
        content_type="multipart/form-data",
    )


def test_stylesheet_is_served(client):
    response = client.get("/static/css/style.css")
    assert response.status_code == 200
    assert b"--blue" in response.data


@pytest.mark.parametrize("name", ["upload.js", "charts.js"])
def test_scripts_are_served(client, name):
    response = client.get(f"/static/js/{name}")
    assert response.status_code == 200
    assert b"addEventListener" in response.data


def test_index_page_has_no_inline_style_or_script(client):
    html = client.get("/").data
    assert b"<style>" not in html
    assert b"<script>" not in html
    assert b"css/style.css" in html
    assert b"js/upload.js" in html


def test_results_page_has_no_inline_style_block(client):
    html = results_page(client).data
    assert b"<style>" not in html
    assert b"css/style.css" in html


def test_plotly_loads_before_the_charts(client):
    html = results_page(client).data
    assert html.index(b"/plotly.js") < html.index(b'id="charts-box"')
    # Each chart fragment calls Plotly as soon as it is parsed.
    assert html.index(b"/plotly.js") < html.index(b"Plotly.newPlot")


def test_results_page_links_the_charts_script(client):
    html = results_page(client).data
    assert b"js/charts.js" in html