import argparse
from datetime import datetime

from . import config as cfg
from .report import launch
from .retrieval import retrieval as r
from .retrieval.batch import available_times, run_range


def main() -> None:
    p = argparse.ArgumentParser(description="Fetch PAFA radiosonde, ERA5, HRRR-AK for one time (UTC)")
    p.add_argument("when", nargs="?", help="single time, e.g. 2025-08-22T12")
    p.add_argument("--range", nargs=2, metavar=("START", "END"),
                help="inclusive range, e.g. 2025-08-15T00 2025-08-21T12")
    p.add_argument("--hours", nargs="+", type=int, default=list(cfg.HOURS),
                   help="launch hours (UTC) to include in --range")
    p.add_argument("--force", action="store_true", help="redo times that already have images")
    p.add_argument("--view", action="store_true", help="open the viewer after a --range run")
    p.add_argument("--view-only", action="store_true", help="open the viewer without fetching anything")
    p.add_argument("--only", choices=["radio", "era5", "hrrr"], help="run a single source")
    p.add_argument("--profiles", action="store_true", help="build standardized profile CSVs for all three sources")
    p.add_argument("--analyze", action="store_true", help="Skew-T and difference plots")
    p.add_argument("--igra-cache", action=argparse.BooleanOptionalAction, default=None,
                   help="use a local copy of the IGRA2 station file (several hundred MB); "
                        "--no-igra-cache forces siphon. Default comes from FC_USE_IGRA_CACHE")
    
    args = p.parse_args()
    if args.igra_cache is not None:
        cfg.USE_IGRA_CACHE = args.igra_cache

    if args.range:
        start, end = (datetime.fromisoformat(s) for s in args.range)
        if start > end:
            p.error("START must be before END")
        hours = tuple(args.hours)
        if args.view_only:
            times = available_times(start, end, hours)
        else:
            times = run_range(start, end, hours, force=args.force)
        if args.view or args.view_only:
            launch(times)
        return

    if not args.when:
        p.error("give a time, or use --range START END")

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