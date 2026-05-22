import pandas as pd
import os
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
INPUT_FOLDER = os.path.join( PROJECT_ROOT, "data", "raw", "air_quality")
OUTPUT_FOLDER = os.path.join(PROJECT_ROOT,"data","processed","cleaned_data")

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Clean Pollutants
def normalize_pollutant(name):
    name = str(name).lower().strip()

    if "nitrogen dioxide" in name or "no2" in name:
        return "NO2"
    elif "pm2.5" in name:
        return "PM2.5"
    elif "pm10" in name:
        return "PM10"
    elif "ozone" in name:
        return "Ozone"
    elif "sulfur dioxide" in name or "so2" in name:
        return "SO2"
    elif "carbon monoxide" in name or name == "co":
        return "CO"
    elif "lead" in name:
        return "Pb"
    else:
        return "Other"

# Cleaning Function
def clean_dataset(filepath):

    df = pd.read_csv(filepath)

    # column names
    df.columns = df.columns.str.strip()

    # text cleaning
    text_cols = ["State Name", "County Name", "City Name", "Parameter Name"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # zero padding on state and county codes
    if "State Code" in df.columns:
        df["State Code"] = df["State Code"].astype(str).str.zfill(2)

    if "County Code" in df.columns:
        df["County Code"] = df["County Code"].astype(str).str.zfill(3)

    # numeric columns to numeric
    numeric_cols = ["Arithmetic Mean", "Latitude", "Longitude"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # standardize missing values
    df.replace(["N/A", "", " "], pd.NA, inplace=True)

    # drop required missing values
    required_cols = ["State Code", "Parameter Name", "Arithmetic Mean"]
    existing_required = [col for col in required_cols if col in df.columns]

    if existing_required:
        df = df.dropna(subset=existing_required)

    # pollutant names
    if "Parameter Name" in df.columns:
        df["pollutant_clean"] = df["Parameter Name"].apply(normalize_pollutant)

        # DROP pollutants that fail normalization
        df = df[df["pollutant_clean"].isin(["Ozone", "PM2.5", "PM10", "NO2", "SO2", "CO", "Pb"])]

        # REPLACE Parameter Name with normalized name
        df["Parameter Name"] = df["pollutant_clean"]

    # remove duplicates
    dedup_cols = ["State Code", "County Code", "Site Num", "Parameter Name", "Year"]
    existing_dedup = [col for col in dedup_cols if col in df.columns]

    if existing_dedup:
        df = df.drop_duplicates(subset=existing_dedup)
    else:
        df = df.drop_duplicates()

    return df

# Process All CSV Files
files = glob.glob(os.path.join(INPUT_FOLDER, "*.csv"))

for file in files:
    print("Processing:", file)

    cleaned_df = clean_dataset(file)

    filename = os.path.basename(file)

    # create new file namee
    year = ''.join(filter(str.isdigit, filename))[:4]
    cleaned_name = f"{year}_clean.csv"

    output_file = os.path.join(OUTPUT_FOLDER, cleaned_name)
    cleaned_df.to_csv(output_file, index=False)

    print("Cleaned:", cleaned_name)

print("All files cleaned.")