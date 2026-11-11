"""
charts.py

Builds the Plotly charts shown on the results page. Each chart is returned
as an HTML fragment. The page loads plotly.js once (served by the app
itself, so no internet connection is needed).
"""

from __future__ import annotations

from typing import Dict, List

import plotly.graph_objects as go

# Muted palette that matches the page (see :root in base.html).
RISK_COLORS = {"LOW": "#3d7a4f", "MEDIUM": "#c28a1d", "HIGH": "#b3402a"}
SMELL_COLORS = ["#2b2926", "#4f6d7a", "#7a8f6a", "#a9826b", "#9a937f"]
INK = "#1f1d1a"
MUTED = "#6b665c"
GRID = "#e2ddd0"
MAX_FILES_SHOWN = 15
MAX_HEATMAP_FILES = 20
CONFIG = {"displayModeBar": False, "responsive": True}
HEATMAP_COLUMNS = ["Model", "Maintainability", "Complexity", "Smells", "Score"]


def _short(path: str) -> str:
    """File name only (long labels squeeze the plot area)."""
    name = path.replace("\\", "/").split("/")[-1]
    return name if len(name) <= 30 else name[:27] + "..."


def _label(f: dict) -> str:
    # The rank prefix keeps labels unique, because Plotly merges duplicate categories.
    return f"{f['rank']}. {_short(f['file'])}"


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def _html(fig: go.Figure) -> str:
    return fig.to_html(full_html=False, include_plotlyjs=False, config=CONFIG)


def _style(fig: go.Figure, title: str, height: int, bargap: float = 0.35) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, x=0, font=dict(size=16, color=INK)),
        height=height,
        margin=dict(l=10, r=50, t=60, b=44),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="ui-monospace, SF Mono, Menlo, Consolas, monospace",
            size=13,
            color=INK,
        ),
        bargap=bargap,
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)
    fig.update_yaxes(zeroline=False, linecolor=GRID)
    return fig


def _bar_height(n: int) -> int:
    return max(380, 44 * n + 150)


def _distribution(gate: dict) -> str:
    order = ("HIGH", "MEDIUM", "LOW")
    counts = [gate["high"], gate["medium"], gate["low"]]
    fig = go.Figure(go.Bar(
        x=list(order),
        y=counts,
        marker_color=[RISK_COLORS[k] for k in order],
        text=counts,
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{x}: %{y} file(s)<extra></extra>",
    ))
    fig.update_yaxes(range=[0, max(counts) * 1.25 + 1])
    if max(counts) <= 10:
        fig.update_yaxes(dtick=1)
    return _html(_style(fig, "How many files at each risk level", 360, bargap=0.6))


def _scores(files: List[dict]) -> str:
    fig = go.Figure(go.Bar(
        x=[f["composite_score"] for f in files],
        y=[_label(f) for f in files],
        orientation="h",
        marker_color=[RISK_COLORS[f["risk_label"]] for f in files],
        text=[f"{f['composite_score']:.3f}" for f in files],
        textposition="outside",
        cliponaxis=False,
        customdata=[f["file"] for f in files],
        hovertemplate="%{customdata}<br>score %{x:.3f}<extra></extra>",
    ))
    fig.add_vline(x=0.33, line_dash="dash", line_color=MUTED,
                  annotation_text="MEDIUM", annotation_position="top")
    fig.add_vline(x=0.66, line_dash="dash", line_color=MUTED,
                  annotation_text="HIGH", annotation_position="top")
    fig.update_xaxes(range=[0, 1.05])
    fig.update_yaxes(autorange="reversed", automargin=True)
    return _html(_style(fig, "Risk score per file", _bar_height(len(files))))


def _complexity(files: List[dict]) -> str:
    values = [f["complexity"] for f in files]
    fig = go.Figure(go.Bar(
        x=values,
        y=[_label(f) for f in files],
        orientation="h",
        marker_color=[RISK_COLORS[f["risk_label"]] for f in files],
        text=values,
        textposition="outside",
        cliponaxis=False,
        customdata=[f["file"] for f in files],
        hovertemplate="%{customdata}<br>complexity %{x}<extra></extra>",
    ))
    fig.add_vline(x=10, line_dash="dash", line_color=MUTED,
                  annotation_text="moderate (10)", annotation_position="top")
    fig.update_xaxes(range=[0, max(12, max(values) * 1.15)])
    fig.update_yaxes(autorange="reversed", automargin=True)
    return _html(_style(fig, "Average complexity per file", _bar_height(len(files))))


def _smells(files: List[dict]) -> str:
    types = sorted({t for f in files for t in f["smell_breakdown"]})
    if not types:
        return "<p>No code smells detected.</p>"
    labels = [_label(f) for f in files]
    fig = go.Figure()
    for i, smell_type in enumerate(types):
        fig.add_bar(
            name=smell_type,
            x=[f["smell_breakdown"].get(smell_type, 0) for f in files],
            y=labels,
            orientation="h",
            marker_color=SMELL_COLORS[i % len(SMELL_COLORS)],
        )
    fig.update_layout(barmode="stack", legend=dict(orientation="h", y=-0.2))
    fig.update_yaxes(autorange="reversed", automargin=True)
    _style(fig, "Smells per file, by type", _bar_height(len(files)) + 50)
    fig.update_layout(margin=dict(l=10, r=50, t=60, b=100))
    return _html(fig)


def _heatmap(files: List[dict]) -> str:
    z, text = [], []
    for f in files:
        # Same normalisation as ml/risk.py compute_risk(): keep the two in sync.
        ml = (f["large_class_probability"] + f["long_method_probability"]) / 2
        z.append([
            ml,
            _clamp((100 - f["maintainability_index"]) / 100),
            _clamp(f["complexity"] / 20),
            _clamp(f["code_smells"] / 10),
            f["composite_score"],
        ])
        text.append([
            f"{ml:.2f}",
            f"MI {f['maintainability_index']}",
            f"{f['complexity']}",
            f"{f['code_smells']}",
            f"{f['composite_score']:.3f}",
        ])
    fig = go.Figure(go.Heatmap(
        z=z,
        x=HEATMAP_COLUMNS,
        y=[_label(f) for f in files],
        text=text,
        texttemplate="%{text}",
        colorscale=[[0, "#cfe0cf"], [0.5, "#ecd9a0"], [1, "#b3402a"]],
        zmin=0,
        zmax=1,
        colorbar=dict(title=dict(text="risk"), thickness=14, len=0.9),
        hovertemplate="%{y}<br>%{x}: %{text}<extra></extra>",
    ))
    fig.update_yaxes(autorange="reversed", automargin=True)
    return _html(_style(fig, "What drives each file's score (0 = low risk, 1 = high risk)",
                        _bar_height(len(files)) + 30))


def build_charts(result: dict) -> Dict[str, str]:
    """Return HTML fragments for each chart, or an empty dict if there are no files."""
    files = result["files"]
    if not files:
        return {}
    top = files[:MAX_FILES_SHOWN]
    note = ""
    if len(files) > MAX_FILES_SHOWN:
        note = (f"Per-file charts show the top {MAX_FILES_SHOWN} of {len(files)} files "
                f"by risk (heatmap: top {MAX_HEATMAP_FILES}).")
    return {
        "distribution": _distribution(result["quality_gate"]),
        "scores": _scores(top),
        "complexity": _complexity(top),
        "smells": _smells(top),
        "heatmap": _heatmap(files[:MAX_HEATMAP_FILES]),
        "note": note,
    }