# planetaryboundaries
Code repository for processing Global Forest Change data from [Hansen et al. (2013)](https://www.science.org/doi/10.1126/science.1244693), exporting multiband rasters and area statistics from Google Earth Engine, and plotting figures for the land system change planetary boundary. 

Contributions for Shahi et al. (in prep)


## Data

Data required to run the analysis is downloaded from the Google Earth Engine asset 'UMD/hansen/global_forest_change_2025_v1_13' using continent extents from [ESRI World Continents](https://hub.arcgis.com/datasets/esri::world-continents/explore) and biome extents from Shahi and Stenzel. 


## Dependencies

Project dependencies are listed in [`requirements.txt`](requirements.txt). 


## Running the workflow

The workflow has two stages: processing data in Google Earth Engine (`a1`, `a2`), and plotting figures (`b1`, `b2`). Run all commands from the repository root.

| Script | Purpose |
|---|---|
| [`a1_gee_hansen_map.py`](src/a1_gee_hansen_map.py) | Aggregates forest loss to 0.25° and exports multiband rasters per continent to the Google Drive folder: `hansen025deg` |
| [`a2_gee_hansen_area.py`](src/a2_gee_hansen_area.py) | Calculates forest loss per biome and continent at 30 m and exports area to the Google Drive folder: `hansen30m` |
| [`b1_plot_hansen_map.py`](src/b1_plot_hansen_map.py) | Plots the 0.25° loss map and exports to `data/figures/hansen_lossyear_025deg.png` |
| [`b2_plot_hansen_area.py`](src/b2_plot_hansen_area.py) | Plots the area statistics ane exports to `data/figures/hansen_remainingforestcover_30m.png` |

### 1. Set up working directory

Run [`0_setup_directory.py`](src/0_setup_directory.py) or manually create the folders: `data`, `data/figures`, `data/hansen_gee_025deg`, `data/hansen_gee_30m`

```bash
python src/0_setup_directory.py
```

### 2. Set up Google Earth Engine

1. Sign up for Earth Engine at https://code.earthengine.google.com/register (free for non-commercial use) and create or select a Google Cloud project with the Earth Engine API enabled. Note your **project ID**.
2. Authenticate once on your machine:

   ```bash
   earthengine authenticate
   ```
   A browser window opens for you to log in. The scripts also call authentication automatically if no stored credentials are found.

### 3. Process Hansen data in Google Earth Engine

Replace `your-gee-project` with your own project ID:

```bash
python src/a1_gee_hansen_map.py --project your-gee-project
python src/a2_gee_hansen_area.py --project your-gee-project
```

These scripts only **start export tasks** on Google's servers. Monitor progress in the [Earth Engine Task Manager](https://code.earthengine.google.com/tasks); large exports can take from minutes to hours.

### 4. Download the exports

When the tasks have finished, download the files from your Google Drive to the following folders:

| Drive folder | Contents | Download to |
|---|---|---|
| `hansen025deg` | 6 GeoTIFFs (`af`, `as`, `eu`, `na`, `oc`, `sa`) | `data/hansen_gee_025deg/` |
| `hansen30m` | 14 CSVs (8 biomes + 6 continents) | `data/hansen_gee_30m/` |

### 5. Plot results

Then run the plotting scripts:

```bash
python src/b1_plot_hansen_map.py
python src/b2_plot_hansen_area.py
```

Figures are saved to `data/figures/`.

