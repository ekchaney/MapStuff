# AQI & Population Density Data Visualization by Team 3
  
CMSC 436 Data Visualization   
Spring 2026  
Team 3 Group Project  
  
  
  Hello user! Thank you for using our interactive United States Population + Air Quality map. In
this map, much information can be learned about Air Quality (measured via the air quality index)
within the continental United States. There are many built-in features that support this, such as
the time slider, layer toggle box, and twinned view pane. Additionally, the ability to zoom in and
hover over specific AQI data collection sites allows for information such as the main pollutant to
be seen. Overall the goal of this map is to inform the average US citizen about AQI over time,
and potential drivers of pollutants so that they feel empowered to discuss with their
governmental representatives if needed.

## Contact Information
#### Name - email (github)  
Bima Prastya - bimap1@umbc.edu (BimaPDev)  
Corey Benjamin - cbenjam1@umbc.edu (corebenj)  
Emma Chaney - echaney2@umbc.edu (ekchaney)  
Nicolas Bartolomeo - nicolab2@umbc.edu (nicobartolomeo)  

## Files 
This directory contains all the files necessary for creating and running the data visualization from scratch. 
Below is a breakdown of the directory structure (and description of materials inside).

MapStuff/  
│  
├── README.md (this file)  
├── LICENSE.txt (licencing for the libraries used)  
├── contact_info.txt (contact info for all developers)  
│  
├── data/  
|   ├── data_sources.txt (explination of our data sources)  
│   │  
│   ├── raw/   
│   │   │  
│   │   ├── air_quality/  
│   │   │   └── *.csv (yearly EPA CSV files)  
│   │   │  
│   │   ├── population/    
│   │   │   ├── *.csv (USA 2000,2020, 2024 census data)  
│   │   │   └── 2024_Gaz_place_national.zip  
│   │   │  
│   │   └── wind/  
│   │       ├── isd-history.csv (NOAA data station registry)  
│   │       └── *.gz (wind vector source files)  
│   │  
│   └── processed/  
│       │  
│       ├── cleaned_data/ (cleaned AQI data)  
│       │   ├── 2000_clean.csv  
│       │   ├── 2001_clean.csv  
│       │   ├── ...  
│       │   └── 2025_clean.csv  
│       │  
│       ├── historical.js (yearly air quality monitoring site data)  
│       ├── population.js (Census population data for cities/places across years)  
│       ├── sites.js (static EPA monitoring site locations)  
│       ├── sites.json (raw JSON version of EPA monitoring site locations)  
│       └── wind.js (2024 wind vector fields)  
│  
├── code/  
│   │  
│   └── preprocessing/  
│       ├── data_cleaning.py (creates the cleaned_data csv files)  
│       ├── generate_historical.py (generates historical.js)  
│       ├── generate_population.py (generates population.js)  
│       └── download_wind.py (generatees wind.js)  
│     
├── figures/  
│   ├── Team_3_Executive_Summary.pdf  (Project Summary)  
│   └── Team_3_Figures_and_Captions.pdf (Figures of project results)  
│  
├── guides/   
│   ├── installation.md  
│   └── user_guide.md  
│  
└── web/  
    │  
    ├── index.html (code that generates the website)  
    │  
    └── assets/  
        │  
        └── glyphs/  
            ├── car.png (hand drawn glyph of a car)  
            ├── ind.png (hand drawn glyph of a factory)  
            ├── ag.png  (hand drawn glyph of a plant)  
            └── atmos.png (hand drawn glyph of a sun)  

## Running the Visualization  
For more information about running the code, see the '../guides' folder 
  
### Licencing Information  
This project is an independent academic visualization and is not affiliated with or endorsed by the EPA, NOAA, or the U.S. Census Bureau.  
  
Processed datasets and visualizations are derived from publicly available government data sources, for more information about this, see 'data/data_sources.txt'  
  
This project also uses the following open-source libraries distibuted under respective open-source licenses:
- MapLibre GL JS — https://maplibre.org/  
- Three.js — https://threejs.org/  
  
Satellite imagery tiles provided by Esri.  

