from datetime import datetime, timedelta

import matplotlib
import traceback

matplotlib.use("Agg")  # batch runs never open plot windows

from .analysis import IMG_DIR, plot_differences, plot_skewt  # noqa: E402
from .profiles import PROFILE_DIR, build_profiles  # noqa: E402

SOURCES = ("radiosonde", "era5", "hrrr")


def launch_times(start: datetime, end: datetime, hours=(0, 12)) -> list[datetime]:
    """Every launch time from start to end, inclusive (default 00 and 12 UTC)."""
    times = []
    day = start.replace(hour=0, minute=0, second=0, microsecond=0)
    while day <= end:
        for h in sorted(hours):
            t = day.replace(hour=h)
            if start <= t <= end:
                times.append(t)
        day += timedelta(days=1)
    return times


def image_paths(dt: datetime):
    """(skew-t, differences) PNG paths for one launch time."""
    return (IMG_DIR / f"skewt_{dt:%Y%m%d%H}.png",
            IMG_DIR / f"diffs_{dt:%Y%m%d%H}.png")


def _has_images(dt: datetime) -> bool:
    return all(p.exists() for p in image_paths(dt))


def _has_profiles(dt: datetime) -> bool:
    return all((PROFILE_DIR / f"{s}_pafa_{dt:%Y%m%d%H}.csv").exists() for s in SOURCES)


def available_times(start: datetime, end: datetime, hours=(0, 12)) -> list[datetime]:
    """Launch times in the range that already have both images."""
    return [t for t in launch_times(start, end, hours) if _has_images(t)]


def run_range(start: datetime, end: datetime, hours=(0, 12), force=False) -> list[datetime]:
    """Build profiles and plots for every launch in the range.

    Times that already have images are skipped unless force=True, so an
    interrupted run can simply be started again. One failure never stops
    the run; failures are listed at the end.
    """
    times = launch_times(start, end, hours)
    ok, skipped, failed = [], [], []

    for i, dt in enumerate(times, 1):
        print(f"\n[{i}/{len(times)}] {dt:%Y-%m-%d %H} UTC")
        if not force and _has_images(dt):
            print("  images exist, skipping")
            skipped.append(dt)
            continue
        try:
            if force or not _has_profiles(dt):
                build_profiles(dt)
            plot_skewt(dt, show=False)
            plot_differences(dt, show=False)
            ok.append(dt)
        except Exception as e:  # missed launch, network error, request timeout...
            msg = repr(e)
            print(f"  FAILED: {msg}")
            traceback.print_exc(limit=-3)
            failed.append((dt, msg))

    print(f"\nDone: {len(ok)} new, {len(skipped)} skipped, {len(failed)} failed")
    for dt, msg in failed:
        print(f"  {dt:%Y-%m-%d %H}: {msg}")

    return available_times(start, end, hours)
