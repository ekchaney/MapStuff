# 'Installation' Guide

## Required Dependencies
To view the project, you need:  
- A modern web browser, such as Chrome, Firefox, or Edge  
- Python 3 installed locally  
- Internet access for loading map tiles and external libraries  
  
The visualization uses the following browser libraries:  
- MapLibre GL JS  
- Three.js  

## How to Load the Project

This is what you need to do if you want to run the project.   
Any steps outside of this section are if you get errors from dependancies.   
   
1. Open the project root folder in terminal.    
2. Type `python -m http.server 8000` and hit enter.  
3. Open up a modern web browser, and navigate to http://localhost:8000/web/  
4. You may now operate the program. See `user_guide` for more details on interaction.  
5. When finished you should stop the execution in terminal with `Ctrl+C`  


## How to Regenerate Processed Data  

The processed visualization files can be rebuilt from the raw datasets using the preprocessing scripts.   
  
Processed outputs include: `historical.js`, `population.js`, `sites.js`, `sites.json`, `wind.js`.  

1. Open the project root folder in terminal.  
2. (Optional) Delete existing program with `rm -rf data/processed/*`  
3. *Clean EPA Air Quality Data* (+ data/processed/cleaned_data/) with `python code/preprocessing/data_cleaning.py`.  
4. *Generate Historical Air Quality Data* (+ data/processed/historical.js) with `python code/preprocessing/generate_historical py`
5. *Generate Population Visualization Data* (+ data/processed/population.js) with `python code/preprocessing/generate_population.py`.
6. *Generate Wind Visualization Data* (+ data/processed/wind.js) with `python code/preprocessing/download_wind.py`.
7. Verify generated files exist in data/processed/.
8. Start the local web server with `python -m http.server 8000`.
9. Open the visualization in browser at http://localhost:8000/web/.
