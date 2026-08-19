# -------------------------------------------------------------------------
# IMPORT PACKAGES
# -------------------------------------------------------------------------
# Standard packages
import os
import pandas as pd
import geopandas as gpd
import numpy as np
import s3fs
import rioxarray as rxr
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from shapely.geometry import box

# EOSTAC packages
from eoforeststac.providers.zarr import ZarrProvider
from eoforeststac.providers.discovery import DiscoveryProvider
from eoforeststac.providers.subset import subset
from eoforeststac.providers.align import DatasetAligner

# Change working directory
os.chdir(r"Z:\person\graham\projectdata\planetary-boundaries")

# Initialize link to gfz s3 bucket through eostac
provider = ZarrProvider(
    catalog_url="https://s3.gfz-potsdam.de/dog.atlaseo-glm.eo-gridded-data/collections/public/catalog.json",
    endpoint_url="https://s3.gfz-potsdam.de",
    anon=True,
)

# Read gfc data from provider
gfc = provider.open_dataset(collection_id="HANSEN_GFC", version='1.12')


# -------------------------------------------------------------------------
# TRY ON SMALL AREA
# -------------------------------------------------------------------------
# Dummy bbox
gdf = gpd.GeoDataFrame(geometry=[box(-55, -15, -45, -10)], crs="EPSG:4326")
geometry = gdf.geometry

# Read data
aoi_lossyear = subset(gfc['loss_year'], geometry=geometry)
aoi_treecover = subset(gfc['tree_cover'], geometry=geometry)

# Summarize
lossyear_summary = pd.DataFrame({'values': np.unique(aoi_lossyear.values, return_counts=True)[0], 
                                 'counts': np.unique(aoi_lossyear.values, return_counts=True)[1]})

# Initialize figure
fig, ax = plt.subplots(figsize=(8, 7), constrained_layout=True)

# Define color palette: no loss (grey), loss years (plasma colormap)
loss_colors = ["#e0e0e0"] + [plt.cm.plasma(i/(22)) for i in range(23)]
loss_cmap = mcolors.ListedColormap(loss_colors)

# Define bounds
bounds = np.arange(-0.5, 23 + 1.5, 1)
loss_norm = mcolors.BoundaryNorm(bounds, loss_cmap.N)

ly_plot = aoi_lossyear.plot(ax=ax, cmap=loss_cmap, norm=loss_norm, add_colorbar=False)

# Add colorbar
cbar = fig.colorbar(ly_plot, ax=ax, fraction=0.046, pad=0.04, ticks=[0, 5, 10, 15, 20, 23])
cbar.ax.set_yticklabels(["No loss", "2005", "2010", "2015", "2020", "2023"])
cbar.set_label("Loss year")

# Add labels
ax.set_title("Hansen GFC v1.12 — Forest Loss Year")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_aspect("equal")

plt.show()


h, w = aoi_lossyear.shape
dpi = 100
fig = plt.figure(frameon=False, figsize=(w / dpi, h / dpi), dpi=dpi)
ax = plt.Axes(fig, [0.0, 0.0, 1.0, 1.0])
ax.set_axis_off()
fig.add_axes(ax)
aoi_lossyear.plot(cmap="Greens", add_colorbar=False)

ax.set_title("2016 estimated aboveground biomass")
plt.show();


# -------------------------------------------------------------------------
# TRY GLOBAL
# -------------------------------------------------------------------------
# Extract lossyear, coarsened to 500m resolution
lossyear_500m = (gfc["loss_year"].coarsen(latitude=(500/30), longitude=(500/30), 
    boundary="trim").min())

# wrap into dask function xarray

"""
read into dask for resampling
look at coarsen code from simon
setup on slurm cluster
1000 tiles, split work, csvs per tile
"""
test = lossyear.where(gfc_canopy > 30, drop=True)


# Extract lossyear array
lossyear_array = lossyear.compute()

# Mask out 0
lossyear_masked = lossyear_array.where(lossyear_array > 0)


# SIMON METHOD
ds_ = xr.open_zarr('https://s3.gfz-potsdam.de/dog.atlaseo-glm.eo-gridded-data/collections/HANSEN_GFC/HANSEN_GFC_v1.12.zarr')
factor = 500
coarse_biomass = (
    ds_.loss_year.coarsen(dim={"longitude": factor, "latitude": factor}, boundary="trim").mean().compute()
)


h, w = coarse_biomass.shape
dpi = 100
fig = plt.figure(frameon=False, figsize=(w / dpi, h / dpi), dpi=dpi)
ax = plt.Axes(fig, [0.0, 0.0, 1.0, 1.0])
ax.set_axis_off()
fig.add_axes(ax)
coarse_biomass.plot(cmap="Greens", add_colorbar=False)

ax.set_title("2016 estimated aboveground biomass")
plt.show();










