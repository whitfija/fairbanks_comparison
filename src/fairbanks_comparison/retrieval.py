from datetime import datetime
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

STATION = "PAFA"
LAT, LON = 64.82, -147.88
AREA = [66.0, -149.5, 63.5, -146.0]  # N, W, S, E
LEVELS = ["1", "2", "3", "5", "7", "10", "20", "30", "50", "70", "100", "125",
          "150", "175", "200", "225", "250", "300", "350", "400", "450", "500",
          "550", "600", "650", "700", "750", "775", "800", "825", "850", "875",
          "900", "925", "950", "975", "1000"]


def get_radiosonde(dt: datetime):
    from siphon.simplewebservice.wyoming import WyomingUpperAir
    df = WyomingUpperAir.request_data(dt, STATION)
    df.to_csv(DATA_DIR / f"radio_{STATION}_{dt:%Y%m%d%H}.csv", index=False)
    return df


def get_era5(dt: datetime):
    import cdsapi
    out = DATA_DIR / f"era5_{dt:%Y%m%d%H}.nc"
    if not out.exists():
        cdsapi.Client().retrieve(
            "reanalysis-era5-pressure-levels",
            {
                "product_type": "reanalysis",
                "variable": ["temperature", "specific_humidity",
                             "relative_humidity", "geopotential"],
                "pressure_level": LEVELS,
                "year": f"{dt:%Y}", "month": f"{dt:%m}", "day": f"{dt:%d}",
                "time": f"{dt:%H}:00",
                "area": AREA,
                "data_format": "netcdf",
            },
            str(out),
        )
    return out


def get_hrrr(dt: datetime):
    from herbie import Herbie
    H = Herbie(f"{dt:%Y-%m-%d %H:00}", model="hrrrak", product="prs", fxx=0,
               save_dir=DATA_DIR / "herbie")
    print(H.inventory())
    return H.xarray(r":(TMP|DPT|RH|HGT):\d+ mb")