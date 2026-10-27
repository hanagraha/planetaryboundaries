"""
Plot the forest loss from Hansen at 0.25 degrees, using pre-processed
classifications of forest cover and disturbance year for visualization
from a1_gee_hansen_map.py, where: 

Forest: if >30% of the 0.25deg tile contains forest cover
Disturbed: if >10% of forest in a forested tile is disturbed
Lossyear: majority (mode) lossyear within disturbance in that tile

"""

# Import packages
import numpy as np
import rasterio
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import cartopy.crs as ccrs
import cartopy.feature as cfeature   


# ----------------------------------------------------------------------
# READ DATA
# ----------------------------------------------------------------------
# Define function to read and combine list of tifs
def load_mosaic(paths, nodata=0):

    # Lazy read for pixel metadata
    infos = []
    for p in paths:
        with rasterio.open(p) as src:
            infos.append((src.bounds, src.res, src.crs))

    # Get pixel size from first tif
    res = infos[0][1]

    # Get extent of all tifs combined
    left = min(b.left for b, _, _ in infos)
    right = max(b.right for b, _, _ in infos)
    bottom = min(b.bottom for b, _, _ in infos)
    top = max(b.top for b, _, _ in infos)

    # Get extent size in pixels (extent in degrees / pixel size in degrees)
    width = int(round((right - left) / res[0]))
    height = int(round((top - bottom) / res[1]))

    # Initialize empty mosaic
    mosaic = np.full((height, width), nodata, dtype=np.uint8)

    # Iterate over each image and read
    for p in paths:
        with rasterio.open(p) as src:

            # Read classification band
            arr = src.read(src.descriptions.index('lossyear025') + 1)

            # Get image position relative to mosaic extent
            col = int(round((src.bounds.left - left) / res[0]))
            row = int(round((top - src.bounds.top) / res[1]))

            # Get image shape
            h, w = arr.shape

            # Select matching mosaic position
            window = mosaic[row:row + h, col:col + w]

            # Write non-na values from image
            valid = arr != nodata
            window[valid] = arr[valid]

    # Bounds in [west, east, south, north] order
    extent = [left, right, bottom, top]

    return mosaic, extent

# Define file paths
continents = ["af", "as", "eu", "na", "oc", "sa"]
tifpaths = [f"data/hansen_gee_025deg/{c}_lossdistribution_025.tif" for c in continents]

# Read data
mosaic, extent = load_mosaic(tifpaths)

# Define layers for plotting
na = mosaic == 0
ones = np.ones_like(mosaic)
loss = np.ma.masked_where(na | (mosaic == 99) | (mosaic == 100), mosaic)  
nonforest = np.ma.masked_where(mosaic != 99, ones)                       
stable = np.ma.masked_where(mosaic != 100, ones)                           


# ----------------------------------------------------------------------
# PLOT
# ----------------------------------------------------------------------
# Initialize figure and projection
fig = plt.figure(figsize=(12, 5.5))
ax = fig.add_axes([0.17, 0.03, 0.81, 0.92], projection=ccrs.Robinson())

# Set global extent
ax.set_global()
 
# Add ocean color
ax.add_feature(cfeature.OCEAN.with_scale("110m"), facecolor='#e8f3fa',
               edgecolor="none", zorder=0)

# Create setting dictionary
kw = dict(origin="upper", extent=extent, transform=ccrs.PlateCarree(),
          interpolation="nearest", zorder=1)
 
# Add stable classes
ax.imshow(nonforest, cmap=ListedColormap(['#e6e6e6']), vmin=0, vmax=1, **kw)
ax.imshow(stable, cmap=ListedColormap(['#a8d5a2']), vmin=0, vmax=1, **kw)

# Add forest loss
im = ax.imshow(loss, cmap='YlOrRd', vmin=1, vmax=25, **kw)
 
# Coastlines
ax.add_feature(cfeature.COASTLINE.with_scale("110m"), linewidth=0.5,
               edgecolor="black", zorder=2)

# Add country borders
ax.add_feature(cfeature.BORDERS.with_scale("110m"), linewidth=0.3,
               edgecolor="black", zorder=2)

# Set line width
ax.spines["geo"].set_linewidth(0.6)
 
# Create colorbar legend
cax = fig.add_axes([0.08, 0.12, 0.02, 0.72])
cb = fig.colorbar(im, cax=cax, orientation="vertical", ticks=[1, 5, 10, 15, 20, 25])
cb.ax.yaxis.set_ticks_position("right")
cb.ax.yaxis.set_label_position("left")
cb.set_label('Year of dominant forest loss', fontsize=13)
cb.ax.set_yticklabels([str(2000 + t) for t in [1, 5, 10, 15, 20, 25]])
cb.ax.tick_params(labelsize=12, width=0.8, length=4)
cb.outline.set_linewidth(0.8)

# Save figure 
fig.savefig("data/figures/hansen_lossyear_025deg.png" , dpi=300, bbox_inches="tight")
print('figure saved to data/figures/hansen_lossyear_025deg.png')
plt.close(fig)