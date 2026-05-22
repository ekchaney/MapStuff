import pandas as pd
import os
import glob
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
CLEANED_DIR = os.path.join( PROJECT_ROOT, "data", "processed", "cleaned_data")
OUTPUT_FILE = os.path.join( PROJECT_ROOT, "data", "processed", "historical.js")
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

POLLUTANTS = ["PM2.5", "Ozone", "PM10", "NO2", "SO2", "CO"]

def pm25_aqi(val):
    if val is None or pd.isna(val): return None
    if val <= 12.0:   return round(val / 12.0 * 50)
    if val <= 35.4:   return round(50 + (val - 12.0) / 23.4 * 50)
    if val <= 55.4:   return round(100 + (val - 35.4) / 20.0 * 50)
    if val <= 150.4:  return round(150 + (val - 55.4) / 95.0 * 50)
    if val <= 250.4:  return round(200 + (val - 150.4) / 100.0 * 100)
    return 301

def ozone_aqi(val_ppm):
    if val_ppm is None or pd.isna(val_ppm): return None
    val = val_ppm * 1000  # convert to ppb
    if val <= 54:    return round(val / 54 * 50)
    if val <= 70:    return round(50 + (val - 54) / 16 * 50)
    if val <= 85:    return round(100 + (val - 70) / 15 * 50)
    if val <= 105:   return round(150 + (val - 85) / 20 * 50)
    if val <= 200:   return round(200 + (val - 105) / 95 * 100)
    return 301

all_years = {}

files = sorted(glob.glob(os.path.join(CLEANED_DIR, "*_clean.csv")))
for file in files:
    year = int(os.path.basename(file)[:4])
    print(f"Processing {year}...")

    df = pd.read_csv(file, low_memory=False)
    df.columns = df.columns.str.strip()

    needed = ["Latitude", "Longitude", "Parameter Name", "Arithmetic Mean", "State Name", "Local Site Name", "County Name"]
    if not all(c in df.columns for c in needed):
        print(f"  Skipping {year}: missing columns")
        continue

    df = df[needed].dropna(subset=["Latitude", "Longitude", "Arithmetic Mean"])
    df = df[df["Parameter Name"].isin(POLLUTANTS)]

    # Round coords to ~1km precision to merge nearby duplicates
    df["lat_r"] = df["Latitude"].round(3)
    df["lon_r"] = df["Longitude"].round(3)

    pivoted = df.groupby(["lat_r", "lon_r", "Parameter Name", "State Name", "Local Site Name", "County Name"])["Arithmetic Mean"].mean().reset_index()

    sites = {}
    for _, row in pivoted.iterrows():
        key = (row["lat_r"], row["lon_r"])
        if key not in sites:
            sites[key] = {
                "lat": row["lat_r"],
                "lon": row["lon_r"],
                "name": str(row["Local Site Name"]).strip() if pd.notna(row["Local Site Name"]) else "",
                "state": str(row["State Name"]).strip() if pd.notna(row["State Name"]) else "",
                "county": str(row["County Name"]).strip() if pd.notna(row["County Name"]) else "",
            }
        p = row["Parameter Name"]
        v = round(float(row["Arithmetic Mean"]), 4) if pd.notna(row["Arithmetic Mean"]) else None
        sites[key][p] = v

    # Compute AQI from PM2.5 (primary) or Ozone as fallback
    site_list = []
    for s in sites.values():
        if "PM2.5" in s:
            s["aqi"] = pm25_aqi(s["PM2.5"])
            s["aqi_pollutant"] = "PM2.5"
        elif "Ozone" in s:
            s["aqi"] = ozone_aqi(s["Ozone"])
            s["aqi_pollutant"] = "Ozone"
        else:
            s["aqi"] = None
            s["aqi_pollutant"] = None
        site_list.append(s)

    all_years[year] = site_list
    print(f"  {len(site_list)} sites")

print("Writing historical.js...")
js = "const HISTORICAL_DATA = " + json.dumps(all_years, separators=(',', ':')) + ";\n"
with open(OUTPUT_FILE, "w") as f:
    f.write(js)

print(f"Done → {OUTPUT_FILE}")
