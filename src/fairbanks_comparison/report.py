import base64
import json
import os
import webbrowser
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from .batch import image_paths
from .retrieval import DATA_DIR

REPORT_PATH = DATA_DIR / "report.html"


def _src(img: Path, out_dir: Path, embed: bool) -> str:
    if embed:
        return "data:image/png;base64," + base64.b64encode(img.read_bytes()).decode()
    rel = Path(os.path.relpath(img, out_dir)).as_posix()
    return quote(rel)


def build_report(times: list[datetime], out: Path = REPORT_PATH, embed: bool = False) -> Path:
    """Write the HTML page.

    embed=False: the page links to the PNGs in data/img (small file, keep the
    folders together). embed=True: images are inlined as base64, giving one
    self-contained file you can email or move anywhere (a few MB per launch).
    """
    out = Path(out)
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
    html = (TEMPLATE
            .replace("__DATA__", json.dumps(entries))
            .replace("__HOURS__", json.dumps(hours)))
    out.write_text(html, encoding="utf-8")
    return out


def launch(times: list[datetime], embed: bool = False) -> None:
    if not times:
        print("No images to show for that range.")
        return
    path = build_report(times, embed=embed)
    print(f"Report: {path.resolve()}")
    webbrowser.open(path.resolve().as_uri())


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>PAFA: radiosonde vs ERA5 vs HRRR-AK</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root { --bg:#fff; --fg:#1b1b1b; --panel:#f3f3f3; --line:#d0d0d0; --accent:#1f6feb; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#16181d; --fg:#e6e6e6; --panel:#20232a; --line:#3a3f4a; --accent:#58a6ff; }
  }
  * { box-sizing: border-box; }
  html, body { height: 100%; margin: 0; }
  body { display: flex; background: var(--bg); color: var(--fg);
         font: 14px system-ui, -apple-system, "Segoe UI", sans-serif; }
  #side { width: 170px; background: var(--panel); border-right: 1px solid var(--line);
          display: flex; flex-direction: column; }
  #filters { padding: 8px; display: flex; gap: 4px; flex-wrap: wrap; border-bottom: 1px solid var(--line); }
  #list { list-style: none; margin: 0; padding: 0; overflow-y: auto; flex: 1; }
  #list li { padding: 6px 10px; cursor: pointer; }
  #list li:hover { background: var(--line); }
  #list li.active { background: var(--accent); color: #fff; }
  #main { flex: 1; min-width: 0; display: flex; flex-direction: column; padding: 10px 14px; }
  #bar { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
  #title { font-weight: 600; flex: 1; }
  button { background: var(--panel); color: var(--fg); border: 1px solid var(--line);
           border-radius: 4px; padding: 4px 10px; cursor: pointer; font: inherit; }
  button.on { background: var(--accent); color: #fff; border-color: var(--accent); }
  #figs { display: flex; gap: 12px; flex: 1; min-height: 0; align-items: flex-start; }
  .fig { flex: 1 1 0; min-width: 0; text-align: center; }
  .fig img { max-width: 100%; max-height: calc(100vh - 80px); background: #fff; }
  #hint { color: #888; font-size: 12px; }
</style>
</head>
<body>
<div id="side">
  <div id="filters"></div>
  <ul id="list"></ul>
</div>
<div id="main">
  <div id="bar">
    <button id="prev">&larr; Prev</button>
    <button id="next">Next &rarr;</button>
    <span id="title"></span>
  </div>
  <div id="figs">
    <div class="fig"><img id="skew" alt="Skew-T"></div>
    <div class="fig"><img id="diffs" alt="Differences"></div>
  </div>
</div>
<script>
const all = __DATA__;
const hours = __HOURS__;
let shown = all.slice();
let idx = 0;

const $ = id => document.getElementById(id);

function renderList() {
  const list = $('list');
  list.innerHTML = '';
  shown.forEach((e, i) => {
    const li = document.createElement('li');
    li.textContent = e.label;
    li.className = i === idx ? 'active' : '';
    li.onclick = () => go(i);
    list.appendChild(li);
  });
}

function go(i) {
  if (!shown.length) return;
  idx = Math.max(0, Math.min(i, shown.length - 1));
  const e = shown[idx];
  $('title').textContent = e.label + '  (' + (idx + 1) + '/' + shown.length + ')';
  $('skew').src = e.skew;
  $('diffs').src = e.diffs;
  renderList();
  $('list').children[idx].scrollIntoView({ block: 'nearest' });
}

function setFilter(h, btn) {
  shown = h === null ? all.slice() : all.filter(e => e.hour === h);
  document.querySelectorAll('#filters button').forEach(b => b.classList.remove('on'));
  btn.classList.add('on');
  go(0);
}

const f = $('filters');
const mk = (text, h) => {
  const b = document.createElement('button');
  b.textContent = text;
  b.onclick = () => setFilter(h, b);
  f.appendChild(b);
  return b;
};
const allBtn = mk('All', null);
hours.forEach(h => mk(String(h).padStart(2, '0') + 'Z', h));
allBtn.classList.add('on');

$('prev').onclick = () => go(idx - 1);
$('next').onclick = () => go(idx + 1);
document.addEventListener('keydown', ev => {
  if (ev.key === 'ArrowLeft' || ev.key === 'ArrowUp') { go(idx - 1); ev.preventDefault(); }
  if (ev.key === 'ArrowRight' || ev.key === 'ArrowDown') { go(idx + 1); ev.preventDefault(); }
  if (ev.key === 'Home') { go(0); ev.preventDefault(); }
  if (ev.key === 'End') { go(shown.length - 1); ev.preventDefault(); }
});

go(0);
</script>
</body>
</html>
"""
