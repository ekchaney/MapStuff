import json
import os
import zipfile

import pandas as pd


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
RAW_DIR = os.path.join( PROJECT_ROOT, "data", "raw", "population")
OUTPUT_FILE = os.path.join( PROJECT_ROOT, "data", "processed", "population.js")
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

POP_FILE = os.path.join(RAW_DIR, "sub-est2024.csv")
POP_2000_2010_FILE = os.path.join(RAW_DIR, "sub-est00int.csv")
POP_2010_2020_FILE = os.path.join(RAW_DIR, "sub-est2020int.csv")
GAZ_FILE = os.path.join(RAW_DIR, "2024_Gaz_place_national.zip")
YEARS = list(range(2000, 2025))


def read_gazetteer():
    with zipfile.ZipFile(GAZ_FILE) as zf:
        [name] = zf.namelist()
        gaz = pd.read_csv(zf.open(name), sep="\t", dtype={"GEOID": str})
    gaz.columns = [c.strip() for c in gaz.columns]
    gaz["GEOID"] = gaz["GEOID"].str.zfill(7)
    return gaz[["GEOID", "USPS", "INTPTLAT", "INTPTLONG"]]


def main():
    source_files = [
        (POP_2000_2010_FILE, range(2000, 2010)),
        (POP_2010_2020_FILE, range(2010, 2020)),
        (POP_FILE, range(2020, 2025)),
    ]

    place_pop = {}
    names = {}
    for file, years in source_files:
      df = pd.read_csv(
          file,
          encoding="latin1",
          dtype={"STATE": str, "PLACE": str},
          low_memory=False,
      )
      # 162 = incorporated place, 170 = consolidated city.
      df = df[df["SUMLEV"].isin([162, 170])].copy()
      df["GEOID"] = df["STATE"].str.zfill(2) + df["PLACE"].str.zfill(5)

      for _, row in df.iterrows():
          geoid = str(row["GEOID"])
          place_pop.setdefault(geoid, {})
          names[geoid] = (str(row["NAME"]), str(row["STNAME"]))
          for year in years:
              col = f"POPESTIMATE{year}"
              if col in row and pd.notna(row[col]):
                  place_pop[geoid][year] = int(row[col])

    pop = pd.DataFrame(
        [
            {
                "GEOID": geoid,
                "NAME": names.get(geoid, ("", ""))[0],
                "STNAME": names.get(geoid, ("", ""))[1],
                **{f"POPESTIMATE{year}": values.get(year) for year in YEARS},
            }
            for geoid, values in place_pop.items()
        ]
    )

    gaz = read_gazetteer()
    merged = pop.merge(gaz, on="GEOID", how="inner")
    merged = merged.sort_values("POPESTIMATE2024", ascending=False, na_position="last")

    records = []
    for _, row in merged.iterrows():
        pop_by_year = {
            year: int(row[f"POPESTIMATE{year}"])
            for year in YEARS
            if f"POPESTIMATE{year}" in row and pd.notna(row[f"POPESTIMATE{year}"])
        }
        if not pop_by_year:
            continue
        records.append(
            {
                "name": str(row["NAME"]),
                "state": str(row["USPS"]),
                "stateName": str(row["STNAME"]),
                "geoid": str(row["GEOID"]),
                "lon": round(float(row["INTPTLONG"]), 6),
                "lat": round(float(row["INTPTLAT"]), 6),
                "pop": pop_by_year,
            }
        )

    js = (
        "const POPULATION_YEARS = "
        + json.dumps(YEARS, separators=(",", ":"))
        + ";\n\nconst POPULATION_CITIES = "
        + json.dumps(records, separators=(",", ":"))
        + ";\n"
    )
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(js)

    print(f"Wrote {len(records):,} Census places to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
