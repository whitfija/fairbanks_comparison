import zipfile
from datetime import datetime

import numpy as np
import pandas as pd
import xarray as xr

from . import retrieval as r
from .retrieval import DATA_DIR, LAT, LON

G = 9.80665
PROFILE_DIR = DATA_DIR / "profiles"
PROFILE_DIR.mkdir(exist_ok=True)


def dewpoint_from_q(q, p_hPa):
    """Dew point (°C) from specific humidity (kg/kg) and pressure (hPa).
    Vapor pressure from q, then inverted Magnus formula (over water)."""
    e = q * p_hPa / (0.622 + 0.378 * q)   # hPa
    x = np.log(e / 6.112)
    return 243.5 * x / (17.67 - x)

# import metpy.calc as mpcalc
# from metpy.units import units

# def dewpoint_from_q(q, p_hPa):
#     td = mpcalc.dewpoint_from_specific_humidity(
#         p_hPa * units.hPa, q * units("kg/kg"))
#     return td.to("degC").magnitude


def radiosonde_profile(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({
        "pressure_hPa": df["pressure"],
        "height_m": df["height"],
        "temp_C": df["temperature"],
        "dewpoint_C": df["dewpoint"],
    })
    return out.dropna().reset_index(drop=True)


def era5_profile(nc_path) -> pd.DataFrame:
    # if zipfile.is_zipfile(nc_path):
    #     with zipfile.ZipFile(nc_path) as z:
    #         z.extractall(nc_path.parent / (nc_path.stem + "_unzipped"))
    #         nc_path = nc_path.parent / (nc_path.stem + "_unzipped") / z.namelist()[0]

    ds = xr.open_dataset(nc_path)
    col = ds.sel(latitude=LAT, longitude=LON, method="nearest").squeeze()
    p = col["pressure_level"].values.astype(float)
    out = pd.DataFrame({
        "pressure_hPa": p,
        "height_m": col["z"].values / G,
        "temp_C": col["t"].values - 273.15,
        "dewpoint_C": dewpoint_from_q(col["q"].values, p),
    })
    return out.sort_values("pressure_hPa", ascending=False).reset_index(drop=True)


def hrrr_profile(ds: xr.Dataset) -> pd.DataFrame:
    lon0 = LON % 360
    d2 = (ds.latitude - LAT) ** 2 + ((ds.longitude - lon0) * np.cos(np.radians(LAT))) ** 2
    iy, ix = np.unravel_index(int(d2.argmin()), d2.shape)
    col = ds.isel(y=iy, x=ix)
    out = pd.DataFrame({
        "pressure_hPa": col["isobaricInhPa"].values,
        "height_m": col["gh"].values,
        "temp_C": col["t"].values - 273.15,
        "dewpoint_C": col["dpt"].values - 273.15,
    })
    return out.sort_values("pressure_hPa", ascending=False).reset_index(drop=True)


def build_profiles(dt: datetime) -> dict[str, pd.DataFrame]:
    """Fetch (or reuse cached) raw data for all three sources and save a
    standardized profile CSV for each."""
    profiles = {
        "radiosonde": radiosonde_profile(r.get_radiosonde(dt)),
        "era5": era5_profile(r.get_era5(dt)),
        "hrrr": hrrr_profile(r.get_hrrr(dt)),
    }
    for name, df in profiles.items():
        path = PROFILE_DIR / f"{name}_pafa_{dt:%Y%m%d%H}.csv"
        df.to_csv(path, index=False)
        print(f"{name}: {len(df)} levels -> {path}")
    return profiles