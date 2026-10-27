"""
Aggregate Hansen tree cover loss to a 0.25 degree grid, per continent,
and export each result to Google Drive.

Python (earthengine-api) port of the original Code Editor JavaScript:
https://code.earthengine.google.com/3f92f006fecd4687c89377343fdcf224

"""

# Authenticate google earth engine
import ee
ee.Authenticate()
ee.Initialize(project="postdist-regrowth")


# ----------------------------------------------------------------------
#                              READ DATA
# ----------------------------------------------------------------------
# Hansen et al. data
hansen = ee.Image("UMD/hansen/global_forest_change_2025_v1_13")

# Hansen land mask (0 = no data, 1 = land, 2 = water)
land = hansen.select("datamask").eq(1)

# Hansen tree cover loss (0 = no loss, 1-25 = lossyear)
lossyear = hansen.select("lossyear").unmask(0)

# Import continent geometries
geompath = "projects/postdist-regrowth/assets/geometries/"
continents = {
    "af": ee.FeatureCollection(geompath + "geom_africa"),
    "as": ee.FeatureCollection(geompath + "geom_asia"),
    "eu": ee.FeatureCollection(geompath + "geom_europe"),
    "na": ee.FeatureCollection(geompath + "geom_namerica"),
    "oc": ee.FeatureCollection(geompath + "geom_oceania").merge(
        ee.FeatureCollection(geompath + "geom_australia")),
    "sa": ee.FeatureCollection(geompath + "geom_samerica"),
}

# Create 0.25 grid
transform025 = [0.25, 0, -180, 0, -0.25, 90]
globextent = ee.Geometry.Rectangle([-180, -60, 180, 80], "EPSG:4326", False)
globgrid = globextent.coveringGrid(ee.Projection("EPSG:4326", transform025))

# Define year band names for resampling: y2001 ... y2025
yearNames = ee.List.sequence(2001, 2025).map(
    lambda y: ee.String("y").cat(ee.Number(y).int().format())
)

# ----------------------------------------------------------------------
#                      GET HANSEN TREE COVER LOSS
# ----------------------------------------------------------------------
# Define function to convert tree cover to forest cover
def forest_filter(trees):
    """Filter tree patches >0.5ha (6+ pixels)."""
    patch_size = trees.selfMask().connectedPixelCount(maxSize=6, eightConnected=True)
    return patch_size.gte(6).unmask(0)

# Forest: >= 10% canopy, >= 0.5 ha patch, on land
forest = forest_filter(hansen.select("treecover2000").gte(10)).And(land)

# 255 = no data/water, 99 = stable non-forest, 0 = stable forest, 1-25 = loss year
hansen_forestloss = lossyear.where(forest.Not(), 99).where(land.Not(), 255)

# Masks for resampling
hansen_forest = hansen_forestloss.lt(99).rename("forest")
hansen_disturbed = (hansen_forestloss.gt(0).And(hansen_forestloss.lt(99)) \
    .rename("disturbed"))

# Convert lossyear raster to a binary image collection (one band per year)
hansen_lossyear_ic = (ee.ImageCollection.fromImages(ee.List.sequence(1, 25) \
    .map(lambda y: hansen_forestloss.eq(ee.Number(y)).rename("year"))) \
    .toBands().rename(yearNames))

# Combine in image stack
hansenstack = hansen_forest.addBands(hansen_disturbed).addBands(hansen_lossyear_ic)


# ----------------------------------------------------------------------
#                       AGGREGATE TO 0.25 DEG
# ----------------------------------------------------------------------
# Define band names from image stack
bandNames = ee.List(
    ["lossyear025", "forest_fraction", "disturbed_fraction", "forest_disturbed"]
).cat(yearNames)

# Define function to summarize raster values in a given tile
def process_tile(tile):
    """Compute fractions and classification for a single 0.25 degree tile."""

    # Extract singular tile
    tile = ee.Feature(tile)

    # Mean of each band in the tile
    mean = ee.Dictionary(hansenstack.reduceRegion(reducer=ee.Reducer.mean(),
        geometry=tile.geometry(), crs=lossyear.projection(), scale=30,
        maxPixels=5e7, tileScale=4))

    # Fraction values
    frac_forest = ee.Number(mean.get("forest"))
    frac_disturbed = ee.Number(mean.get("disturbed"))
    frac_lossyear = ee.List(yearNames.map(lambda band: mean.get(band)))

    # Forest classification (threshold: >30% of tile = forest)
    mode_forest = frac_forest.gte(0.3)

    # Disturbance classification
    forest_disturbed = ee.Number(ee.Algorithms.If(frac_forest.gt(0), 
        frac_disturbed.divide(frac_forest), 0))

    # Loss year classification (mode year, year with max fraction)
    lossyear_modeval = frac_lossyear.reduce(ee.Reducer.max())
    lossyear_modeindex = frac_lossyear.indexOf(lossyear_modeval)
    mode_lossyear = ee.Number(lossyear_modeindex).add(1)

    # Apply thresholds for visualization
    classification = ee.Number(ee.Algorithms.If(mode_forest,
        ee.Algorithms.If(forest_disturbed.gte(0.1), mode_lossyear, 100), 99))

    # Add properties to tile
    return tile.set({"forest_fraction": frac_forest, "disturbed_fraction": frac_disturbed,
        "forest_disturbed": forest_disturbed, "lossyear025": classification}
    ).set(mean.select(yearNames, True))

# Define function to aggregate raster over a grid
def aggregate(geom):
    """Aggregate raster data over the 0.25 degree grid within a geometry."""

    # Filter global grid for desired geometry / bounds
    grid = globgrid.filterBounds(geom)

    # Summarize raster values per tile
    distribution = grid.map(process_tile)

    # Convert to multiband raster
    def to_band(b):
        b = ee.String(b)
        return distribution.reduceToImage(properties=[b], 
            reducer=ee.Reducer.first()).rename(b)

    # Return as multiband image
    return (ee.ImageCollection(bandNames.map(to_band)).toBands()
        .rename(bandNames).float().reproject(crs="EPSG:4326", 
        crsTransform=transform025).clip(geom)
    )


# ----------------------------------------------------------------------
#                          EXPORT PER CONTINENT
# ----------------------------------------------------------------------

if __name__ == "__main__":

    # Iterate over each continent
    for k, fc in continents.items():

        # Aggregate hansen data to 0.25 degrees
        distimg = aggregate(fc)

        # Export image to Google Drive
        task = ee.batch.Export.image.toDrive(
            image=distimg,
            description=f"{k}_lossdistribution_025",
            folder="hansen025_test",
            crs="EPSG:4326",
            crsTransform=transform025,
            region=fc.geometry(),
            maxPixels=int(1e9)
        )

        # Start export task
        task.start()

        # Print statement
        print(f"Started export task for {k}: {task.id}")