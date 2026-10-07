import argparse
from datetime import datetime

from . import retrieval as r


def main() -> None:
    p = argparse.ArgumentParser(description="Fetch PAFA radiosonde, ERA5, HRRR-AK for one time (UTC)")
    p.add_argument("when", help="e.g. 2023-01-15T12")
    p.add_argument("--only", choices=["radio", "era5", "hrrr"], help="run a single source")
    p.add_argument("--profiles", action="store_true",
               help="build standardized profile CSVs for all three sources")
    p.add_argument("--analyze", action="store_true", help="Skew-T and difference plots")
    args = p.parse_args()
    

    dt = datetime.fromisoformat(args.when)

    if args.profiles:
        from .profiles import build_profiles
        for name, df in build_profiles(dt).items():
            print(f"\n{name}\n{df.head()}")

    if args.analyze:
        from .analysis import plot_differences, plot_skewt
        plot_skewt(dt)
        plot_differences(dt)

    if args.profiles or args.analyze:
        return

    if args.only in (None, "radio"):
        print("Radiosonde...")
        print(r.get_radiosonde(dt).head())
    if args.only in (None, "era5"):
        print("ERA5...")
        print(r.get_era5(dt))
    if args.only in (None, "hrrr"):
        print("HRRR-AK...")
        print(r.get_hrrr(dt))