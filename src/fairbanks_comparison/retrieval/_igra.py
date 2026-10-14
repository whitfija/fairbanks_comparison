import shutil
import time
from datetime import datetime

import numpy as np
import pandas as pd
import requests

from .. import config as cfg

cfg.IGRA_DIR.mkdir(parents=True, exist_ok=True)
TXT = cfg.IGRA_DIR / f"{cfg.IGRA_STATION}-data.txt"
INDEX = cfg.IGRA_DIR / f"{cfg.IGRA_STATION}-index.csv"
URL = f"https://www.ncei.noaa.gov/pub/data/igra/data/data-por/{cfg.IGRA_STATION}-data.txt.zip"
MISSING = {-9999, -8888}


def refresh():
    """Download the station file, unzip it, and rebuild the index."""
    import zipfile
    zpath = cfg.IGRA_DIR / f"{cfg.IGRA_STATION}-data.txt.zip"
    print(f"Downloading {URL}")
    with requests.get(URL, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        with open(zpath, "wb") as f:
            f.writelines(resp.iter_content(1 << 20))
    with zipfile.ZipFile(zpath) as z, z.open(z.namelist()[0]) as src, open(TXT, "wb") as dst:
        shutil.copyfileobj(src, dst)
    zpath.unlink()

    rows, offset = [], 0
    with open(TXT, "rb") as f:
        for line in f:
            if line.startswith(b"#"):
                s = line.decode()
                y, mo, d, h = int(s[13:17]), int(s[18:20]), int(s[21:23]), int(s[24:26])
                nominal = f"{y:04d}-{mo:02d}-{d:02d} {h:02d}:00" if h < 24 else ""
                rows.append((y, mo, d, h, int(s[27:31]), int(s[32:36]), nominal, offset))
            offset += len(line)
    pd.DataFrame(rows, columns=["year", "month", "day", "hour", "reltime",
                                "numlev", "nominal", "offset"]).to_csv(INDEX, index=False)
    print(f"Indexed {len(rows)} soundings -> {INDEX}")


def _index(dt=None) -> pd.DataFrame:
    """Load the index. Only re-download if dt is newer than anything cached
    AND the cached file is over a day old."""
    if TXT.exists() and INDEX.exists():
        idx = pd.read_csv(INDEX, parse_dates=["nominal"])
        stale = (dt is not None and dt > idx["nominal"].max()
                 and time.time() - TXT.stat().st_mtime > 86400)
        if not stale:
            return idx
    refresh()
    return pd.read_csv(INDEX, parse_dates=["nominal"])


def get_sounding(dt: datetime) -> pd.DataFrame:
    idx = _index(dt)
    hit = idx[idx["nominal"] == pd.Timestamp(dt)]
    if hit.empty:
        raise LookupError(f"No IGRA2 sounding for {cfg.IGRA_STATION} at {dt:%Y-%m-%d %H} UTC")
    row = hit.iloc[0]
    with open(TXT, "rb") as f:
        f.seek(int(row["offset"]))
        f.readline()  # skip header
        lines = [f.readline().decode() for _ in range(int(row["numlev"]))]

    def num(s, scale=1):
        v = int(s)
        return np.nan if v in MISSING else v / scale

    recs = []
    for l in lines:
        t = num(l[22:27], 10)                 # tenths of °C
        recs.append((num(l[9:15], 100),       # Pa -> hPa
                     num(l[16:21]),           # geopotential height, m
                     t,
                     t - num(l[34:39], 10)))  # dewpoint = T - dewpoint depression
    return pd.DataFrame(recs, columns=["pressure", "height", "temperature", "dewpoint"])


def check(start: datetime, end: datetime, hours=(0, 12)) -> None:
    """Print which expected launches are in the file, and everything the file
    has for those dates (to catch soundings filed under an odd hour)."""
    idx = _index(end)
    have = set(idx["nominal"].dropna())
    expected = [t for t in pd.date_range(start, end, freq="h") if t.hour in hours]
    missing = [t for t in expected if t not in have]
    print(f"{len(expected) - len(missing)}/{len(expected)} expected launches present")
    for t in missing:
        print(f"  missing: {t:%Y-%m-%d %H} UTC")

    dates = pd.to_datetime(idx[["year", "month", "day"]])
    window = idx[(dates >= pd.Timestamp(start).normalize()) & (dates <= pd.Timestamp(end).normalize())]
    print("\nAll entries in the file for those dates:")
    print(window[["year", "month", "day", "hour", "reltime", "numlev"]].to_string(index=False))


if __name__ == "__main__":
    import sys
    check(datetime.fromisoformat(sys.argv[1]), datetime.fromisoformat(sys.argv[2]))