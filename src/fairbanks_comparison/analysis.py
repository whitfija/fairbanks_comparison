from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from metpy.plots import SkewT
from metpy.units import units

from .profiles import PROFILE_DIR
from .retrieval import DATA_DIR

IMG_DIR = DATA_DIR / "img"
IMG_DIR.mkdir(parents=True, exist_ok=True)
COLORS = {"radiosonde": "black", "era5": "tab:blue", "hrrr": "tab:red"}


def load(name: str, dt: datetime) -> pd.DataFrame:
    return pd.read_csv(PROFILE_DIR / f"{name}_pafa_{dt:%Y%m%d%H}.csv")


def interp_to(p_target, src: pd.DataFrame, cols=("temp_C", "dewpoint_C", "height_m")):
    """Interpolate src onto p_target (hPa) using ln(p). NaN outside src range."""
    s = src.sort_values("pressure_hPa")          # np.interp needs increasing x
    lp = np.log(s["pressure_hPa"].values)
    out = {"pressure_hPa": np.asarray(p_target)}
    for c in cols:
        out[c] = np.interp(np.log(p_target), lp, s[c].values, left=np.nan, right=np.nan)
    return pd.DataFrame(out)


def differences(dt: datetime) -> dict[str, pd.DataFrame]:
    """model minus radiosonde, on each model's own levels."""
    sonde = load("radiosonde", dt)
    diffs = {}
    for name in ("era5", "hrrr"):
        model = load(name, dt)
        ref = interp_to(model["pressure_hPa"].values, sonde)
        d = model.copy()
        for c in ("temp_C", "dewpoint_C", "height_m"):
            d[c] = model[c].values - ref[c].values
        diffs[name] = d.dropna()
    return diffs


def plot_skewt(dt: datetime, show=True):
    fig = plt.figure(figsize=(7, 8))
    skew = SkewT(fig)
    for name, color in COLORS.items():
        df = load(name, dt)
        p = df["pressure_hPa"].values * units.hPa
        skew.plot(p, df["temp_C"].values * units.degC, color=color, lw=1.5, label=f"{name} T")
        skew.plot(p, df["dewpoint_C"].values * units.degC, color=color, ls="--", lw=1.5)
    skew.ax.set_ylim(1050, 100)
    skew.ax.set_xlim(-40, 30)
    skew.plot_dry_adiabats(alpha=0.2)
    skew.plot_moist_adiabats(alpha=0.2)
    skew.ax.legend(loc="upper left")
    skew.ax.set_title(f"PAFA {dt:%Y-%m-%d %H} UTC (solid = T, dashed = Td)")
    fig.savefig(IMG_DIR / f"skewt_{dt:%Y%m%d%H}.png", dpi=150, bbox_inches="tight")
    if show:
        plt.show()


def plot_differences(dt: datetime, show=True):
    diffs = differences(dt)
    fig, axes = plt.subplots(1, 2, figsize=(9, 6), sharey=True)
    for name, d in diffs.items():
        axes[0].plot(d["temp_C"], d["pressure_hPa"], color=COLORS[name], label=name)
        axes[1].plot(d["dewpoint_C"], d["pressure_hPa"], color=COLORS[name], label=name)
    for ax, title in zip(axes, ("Temperature diff (°C)", "Dew point diff (°C)")):
        ax.axvline(0, color="gray", lw=0.8)
        ax.set_yscale("log")
        ax.set_ylim(1050, 100)
        ax.set_title(title + "\nmodel - radiosonde")
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("Pressure (hPa)")
    axes[0].legend()
    fig.savefig(IMG_DIR / f"diffs_{dt:%Y%m%d%H}.png", dpi=150, bbox_inches="tight")
    if show:
        plt.show()