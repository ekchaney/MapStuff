"""
Download NOAA ISD Lite wind data (2000-2025), build annual wind vector grids,
and write data/wind.js for the wind particle visualization.

Requires: numpy
Run once; already-downloaded files are cached in python/wind_raw/.
"""

import argparse
import os
import csv
import gzip
import json
import math
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "wind_raw")
OUTPUT_JS = os.path.join(BASE_DIR, "..", "data", "wind.js")

DEFAULT_YEARS = list(range(2000, 2026))
LAT_MIN, LAT_MAX =  24.5,  49.5
LON_MIN, LON_MAX = -125.0, -66.5
GRID_COLS, GRID_ROWS = 60, 40
SEL_COLS,  SEL_ROWS  = 20, 14   # coarse grid used to pick representative stations

os.makedirs(CACHE_DIR, exist_ok=True)


# ──────────────────────────────────────────────
# Station selection
# ──────────────────────────────────────────────

def fetch_stations():
    path = os.path.join(CACHE_DIR, "isd-history.csv")
    if not os.path.exists(path):
        print("Downloading ISD station history (~5 MB)...")
        urllib.request.urlretrieve(
            "https://www.ncei.noaa.gov/pub/data/noaa/isd-history.csv", path
        )
    stations = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            try:
                lat = float(row["LAT"])
                lon = float(row["LON"])
            except (ValueError, KeyError):
                continue
            if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
                continue
            if row.get("CTRY", "").strip() != "US":
                continue
            usaf = row.get("USAF", "").strip().zfill(6)
            wban = row.get("WBAN", "").strip().zfill(5)
            if usaf in ("999999", "000000"):
                continue
            try:
                begin = int(str(row.get("BEGIN", "0"))[:4] or "0")
                end   = int(str(row.get("END",   "0"))[:4] or "9999")
            except ValueError:
                begin, end = 0, 9999
            if begin > 2025 or end < 2000:
                continue
            stations.append({
                "usaf": usaf, "wban": wban,
                "lat": lat,   "lon": lon,
                "begin": begin, "end": end,
            })
    return stations


def grid_select(stations):
    """Pick one station per coarse lat/lon cell for geographic coverage."""
    lat_step = (LAT_MAX - LAT_MIN) / SEL_ROWS
    lon_step = (LON_MAX - LON_MIN) / SEL_COLS
    grid = {}
    for st in stations:
        c = min(SEL_COLS - 1, int((st["lon"] - LON_MIN) / lon_step))
        r = min(SEL_ROWS - 1, int((st["lat"] - LAT_MIN) / lat_step))
        key = (r, c)
        if key not in grid:
            grid[key] = st
    return list(grid.values())


# ──────────────────────────────────────────────
# Download
# ──────────────────────────────────────────────

def _cache_path(st, year):
    return os.path.join(CACHE_DIR, str(year), f"{st['usaf']}-{st['wban']}-{year}.gz")


def _download(st, year):
    dst = _cache_path(st, year)
    if os.path.exists(dst):
        return True
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    url = (f"https://www.ncei.noaa.gov/pub/data/noaa/isd-lite/"
           f"{year}/{st['usaf']}-{st['wban']}-{year}.gz")
    try:
        urllib.request.urlretrieve(url, dst)
        return True
    except Exception:
        try:
            os.remove(dst)
        except OSError:
            pass
        return False


def download_all(stations, years):
    tasks = [
        (st, yr)
        for st in stations
        for yr in years
        if st["begin"] <= yr <= st["end"]
    ]
    total = len(tasks)
    print(f"Queuing {total} station-year downloads (cached files skipped)...")
    done = [0]

    def _task(args):
        _download(*args)
        done[0] += 1
        if done[0] % 250 == 0:
            print(f"  {done[0]}/{total}")

    with ThreadPoolExecutor(max_workers=30) as ex:
        list(ex.map(_task, tasks))
    print(f"  {total}/{total} done.")


# ──────────────────────────────────────────────
# Parse
# ──────────────────────────────────────────────

def parse_station_year(st, year):
    """Return (u_mean, v_mean) in m/s or None if insufficient data.

    ISD Lite columns (space-separated):
      0:year  1:mon  2:day  3:hour  4:air_temp  5:dew  6:slp
      7:wind_dir(deg, 999=missing)  8:wind_spd(m/s*10, 9999=missing)  ...
    Wind direction is meteorological (direction wind is FROM).
    """
    path = _cache_path(st, year)
    if not os.path.exists(path):
        return None
    u_acc = v_acc = 0.0
    count = 0
    try:
        with gzip.open(path, "rt", errors="replace") as f:
            for line in f:
                parts = line.split()
                if len(parts) < 9:
                    continue
                try:
                    wdir = int(parts[7])
                    wspd = int(parts[8])
                except ValueError:
                    continue
                if wdir == 999 or wspd == 9999:
                    continue
                spd = wspd / 10.0
                rad = math.radians(wdir)
                # Met convention: wdir is direction wind is FROM, so the
                # velocity vector points in the opposite direction.
                u_acc += -spd * math.sin(rad)   # eastward
                v_acc += -spd * math.cos(rad)   # northward
                count += 1
    except Exception:
        return None
    if count < 100:
        return None
    return u_acc / count, v_acc / count


# ──────────────────────────────────────────────
# Grid building
# ──────────────────────────────────────────────

def smooth(arr, passes=3):
    """Box-blur passes to smooth IDW artifacts at grid boundaries."""
    for _ in range(passes):
        p = np.pad(arr, 1, mode="edge")
        arr = (p[1:-1, 1:-1] + p[:-2, 1:-1] + p[2:, 1:-1] +
               p[1:-1, :-2]  + p[1:-1, 2:]) / 5.0
    return arr


def idw_grid(station_data):
    """Inverse-distance-weighted interpolation of station u/v onto output grid."""
    lat_pts = np.linspace(LAT_MIN, LAT_MAX, GRID_ROWS)
    lon_pts = np.linspace(LON_MIN, LON_MAX, GRID_COLS)
    lons_g, lats_g = np.meshgrid(lon_pts, lat_pts)   # (rows, cols)

    if not station_data:
        return np.zeros((GRID_ROWS, GRID_COLS)), np.zeros((GRID_ROWS, GRID_COLS))

    st_lats = np.array([s["lat"] for s in station_data])
    st_lons = np.array([s["lon"] for s in station_data])
    st_u    = np.array([s["u"]   for s in station_data])
    st_v    = np.array([s["v"]   for s in station_data])

    # Broadcast: (rows, cols, n_stations)
    dlat = lats_g[:, :, None] - st_lats[None, None, :]
    dlon = lons_g[:, :, None] - st_lons[None, None, :]
    d2   = np.maximum(dlat**2 + dlon**2, 1e-6)
    w    = 1.0 / d2

    u_grid = (w * st_u).sum(axis=2) / w.sum(axis=2)
    v_grid = (w * st_v).sum(axis=2) / w.sum(axis=2)

    return smooth(u_grid), smooth(v_grid)


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Build data/wind.js from NOAA ISD Lite (cached under python/wind_raw/)."
    )
    parser.add_argument(
        "--years",
        type=int,
        nargs="+",
        metavar="Y",
        help=f"Years to include (default: {DEFAULT_YEARS[0]}-{DEFAULT_YEARS[-1]}). "
        "Smaller sets download faster; the map falls back to synthetic flow for missing years.",
    )
    args = parser.parse_args()
    years_run = sorted(set(args.years)) if args.years else list(DEFAULT_YEARS)

    print("Loading ISD station list...")
    all_stations = fetch_stations()
    selected     = grid_select(all_stations)
    print(f"  {len(selected)} representative stations selected "
          f"from {len(all_stations)} US continental stations")

    download_all(selected, years_run)

    print("Parsing wind data and building grids...")
    year_grids = {}
    year_p95   = []

    for year in years_run:
        station_data = []
        for st in selected:
            result = parse_station_year(st, year)
            if result:
                station_data.append({
                    "lat": st["lat"], "lon": st["lon"],
                    "u": result[0],   "v": result[1],
                })
        u_g, v_g = idw_grid(station_data)
        year_grids[year] = (u_g, v_g)
        p95 = float(np.percentile(np.sqrt(u_g**2 + v_g**2), 95))
        year_p95.append(p95)
        print(f"  {year}: {len(station_data):3d} stations  p95={p95:.3f} m/s")

    # Normalize globally so windy years look windier than calm years.
    # Scale so the 80th percentile of annual p95 values maps to magnitude ~1.
    global_scale = 1.0 / max(float(np.percentile(year_p95, 80)), 0.01)
    print(f"\nGlobal scale: {global_scale:.4f}  "
          f"(p80 of annual p95s = {1/global_scale:.3f} m/s)")

    output = {
        "meta": {
            "cols": GRID_COLS, "rows": GRID_ROWS,
            "latMin": LAT_MIN, "latMax": LAT_MAX,
            "lonMin": LON_MIN, "lonMax": LON_MAX,
        }
    }
    for year, (u_g, v_g) in sorted(year_grids.items()):
        u_s = np.clip(u_g * global_scale, -2.0, 2.0)
        v_s = np.clip(v_g * global_scale, -2.0, 2.0)
        output[str(year)] = {
            "u": [round(float(x), 3) for x in u_s.flatten()],
            "v": [round(float(x), 3) for x in v_s.flatten()],
        }

    print(f"\nWriting {OUTPUT_JS}...")
    with open(OUTPUT_JS, "w") as f:
        f.write("const WIND_DATA = ")
        json.dump(output, f, separators=(",", ":"))
        f.write(";\n")

    size_kb = os.path.getsize(OUTPUT_JS) / 1024
    print(f"Done. wind.js is {size_kb:.0f} KB")


if __name__ == "__main__":
    main()
