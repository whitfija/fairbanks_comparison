import base64
import json
import os
import webbrowser
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from .. import config as cfg
from ..retrieval.batch import image_paths

ASSETS = Path(__file__).parent


def _asset(name: str) -> str:
    return (ASSETS / name).read_text(encoding="utf-8")


def _src(img: Path, out_dir: Path, embed: bool) -> str:
    if embed:
        return "data:image/png;base64," + base64.b64encode(img.read_bytes()).decode()
    rel = Path(os.path.relpath(img, out_dir)).as_posix()
    return quote(rel)


def report_path(times: list[datetime]) -> Path:
    a, b = min(times), max(times)
    return cfg.REPORT_DIR / f"report_{a:%Y%m%d%H}_{b:%Y%m%d%H}.html"


def build_report(times: list[datetime], out: Path | None = None, embed: bool = False) -> Path:
    """Write the HTML page.

    embed=False: the page links to the PNGs in data/img (small file, keep the
    folders together). embed=True: images are inlined as base64, giving one
    self-contained file you can email or move anywhere (a few MB per launch).
    The CSS and JS are always inlined, so the output is one HTML file either way.
    """
    out = Path(out) if out else report_path(times)
    out.parent.mkdir(parents=True, exist_ok=True)

    entries = []
    for dt in times:
        skew, diffs = image_paths(dt)
        entries.append({
            "label": f"{dt:%Y-%m-%d} {dt:%H} UTC",
            "hour": dt.hour,
            "skew": _src(skew, out.parent, embed),
            "diffs": _src(diffs, out.parent, embed),
        })
    hours = sorted({e["hour"] for e in entries})
    span = f"{min(times):%Y-%m-%d %H}Z to {max(times):%Y-%m-%d %H}Z"

    js = (_asset("app.js")
          .replace("__DATA__", json.dumps(entries))
          .replace("__HOURS__", json.dumps(hours)))
    html = (_asset("template.html")
            .replace("__RANGE__", span)
            .replace("__CSS__", _asset("style.css"))
            .replace("__JS__", js))
    out.write_text(html, encoding="utf-8")
    return out


def launch(times: list[datetime], embed: bool = False) -> None:
    if not times:
        print("no images to show for that range.")
        return
    path = build_report(times, embed=embed)
    print(f"report: {path.resolve()}")
    webbrowser.open(path.resolve().as_uri())