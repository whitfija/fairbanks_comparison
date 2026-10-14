from datetime import datetime

import pandas as pd

from .. import config as cfg


def get_radiosonde(dt: datetime):
    if cfg.USE_IGRA_CACHE:
        from ._igra import get_sounding  # lazy: the cache is optional
        df = get_sounding(dt)
    else:
        from siphon.simplewebservice.igra2 import IGRAUpperAir
        try:
            raw, _ = IGRAUpperAir.request_data(dt, cfg.IGRA_STATION)
        except ValueError as e:  # siphon's "No dates match selection"
            raise LookupError(
                f"No IGRA2 sounding for {cfg.IGRA_STATION} at {dt:%Y-%m-%d %H} UTC") from e
        df = pd.DataFrame({c: raw[c] for c in ("pressure", "height", "temperature", "dewpoint")})
    df.to_csv(cfg.RADIO_DIR / f"radio_{cfg.STATION}_{dt:%Y%m%d%H}.csv", index=False)
    return df


def get_era5(dt: datetime):
    import cdsapi
    out = cfg.ERA5_DIR / f"era5_{dt:%Y%m%d%H}.nc"
    if not out.exists():
        cdsapi.Client().retrieve(
            "reanalysis-era5-pressure-levels",
            {
                "product_type": "reanalysis",
                "variable": ["temperature", "specific_humidity",
                             "relative_humidity", "geopotential"],
                "pressure_level": cfg.LEVELS,
                "year": f"{dt:%Y}", "month": f"{dt:%m}", "day": f"{dt:%d}",
                "time": f"{dt:%H}:00",
                "area": cfg.AREA,
                "data_format": "netcdf",
            },
            str(out),
        )
    return out


def get_hrrr(dt: datetime):
    from herbie import Herbie
    H = Herbie(f"{dt:%Y-%m-%d %H:00}", model="hrrrak", product="prs", fxx=0,
               save_dir=cfg.HERBIE_DIR)
    print(H.inventory())
    return H.xarray(r":(TMP|DPT|RH|HGT):\d+ mb")