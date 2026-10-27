"""
Plot remaining forest cover area from Hansen at 30m calculated from 
a2_gee_hansen_area.py

"""

# Import packages
import pandas as pd
import matplotlib.pyplot as plt

# Define color palette
muted = ["#999933", "#E69F00", "#D55E00", "#009E73",
         "#332288", "#0072B2", "#CC79A7", "#117733"]

# Define year range
years = list(range(2000, 2026))


# -------------------------------------------------------------------------
# READ DATA
# -------------------------------------------------------------------------
# Define function to read area, convert to Mha
def readarea(path):
    df = pd.read_csv('data/hansen_gee_30m/' + path).iloc[:, 1:3]
    df['area'] = df['area'] / 1e6
    df = df.set_index("lossyear")["area"]
    return df

# Read loss area (biomes)
borealamerica = readarea("borealamerica_loss.csv")
borealeurasia = readarea("borealeurasia_loss.csv")
temperateamerica = readarea("temperateamerica_loss.csv")
temperateasia = readarea("temperateasia_loss.csv")
temperateeurope = readarea("temperateeurope_loss.csv")
tropicalafrica = readarea("tropicalafrica_loss.csv")
tropicalamerica = readarea("tropicalamerica_loss.csv")
tropicalasia = readarea("tropicalasia_loss.csv")

# Read loss area (continents)
asia = readarea('as_loss.csv')
africa = readarea('af_loss.csv')
samerica = readarea('sa_loss.csv')
namerica = readarea('na_loss.csv')
europe = readarea('eu_loss.csv')
oceania = readarea('oc_loss.csv')
world = asia + africa + samerica + namerica + europe + oceania


# -------------------------------------------------------------------------
# PLOT REMAINING FOREST COVER (PROPORTIONAL)
# -------------------------------------------------------------------------
# Define function to calculate remaining forest area
def propremainingforest(loss):

    # Extract initial forest area and annualloss
    initial_forest = loss.loc[0]
    annual_loss = loss.loc[1:]

    # Calculate remaining forest area
    remaining = initial_forest - annual_loss.cumsum()

    # Calculate proportional remaining forest area
    prop = remaining / initial_forest * 100

    # Add 100% for initial forest area
    prop.loc[0] = 100
    
    return prop.sort_index()

# Compile data into dictionary
propremaining_forest_biomes = {
    "Boreal America": propremainingforest(borealamerica),
    "Boreal Eurasia": propremainingforest(borealeurasia),
    "Temperate America": propremainingforest(temperateamerica),
    "Temperate Asia": propremainingforest(temperateasia),
    "Temperate Europe": propremainingforest(temperateeurope),
    "Tropical Africa": propremainingforest(tropicalafrica),
    "Tropical America": propremainingforest(tropicalamerica),
    "Tropical Asia": propremainingforest(tropicalasia),
    "Global Average": propremainingforest(world)
}

# Define label offests
label_offsets = {
    "Boreal America": 0.0,
    "Boreal Eurasia": -0.7,
    "Temperate America": 0.0,
    "Temperate Asia": 0.5,
    "Temperate Europe": 0.0,
    "Tropical Africa": -0.5,
    "Tropical America": 1.2,
    "Tropical Asia": -0.3,
    "Global Average": -1.4
}

# Plot Global Average on top, styled distinctly
world_data = propremaining_forest_biomes["Global Average"]
world_color = muted[list(propremaining_forest_biomes.keys()).index("Global Average")]

# Initialize figure
fig, ax = plt.subplots(figsize=(10, 5))

# Plot all biomes
for (name, data), color in zip(propremaining_forest_biomes.items(), muted):
    if name == "Global Average":
        continue

    ax.plot(years, data.values, label=name, color=color, 
             linewidth=2, linestyle="--", alpha=0.5)

    ax.text(years[-1] + 0.3, data.values[-1] + label_offsets[name], name, 
            color=color, fontsize=11, va="center", alpha=0.5)

# Plot global average
ax.plot(years, world_data.values, label="Global Average", 
         color=world_color, linewidth=3)
ax.text(years[-1] + 0.3, world_data.values[-1] + label_offsets["Global Average"], 
         "Global Average", color=world_color, fontsize=11, va="center", fontweight="bold")

# Adjust axes labels
ax.set_xlabel("Year", fontsize=14, fontweight='bold')
ax.set_ylabel("% of remaining forest cover from 2000", fontsize=14, fontweight='bold')

# Tick label size
ax.tick_params(axis="both", labelsize=14)

# Add gridlines
ax.grid(axis="y", linestyle="--", alpha=0.3)

# Remove spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Save
plt.tight_layout()
plt.savefig("data/figures/hansen_remainingforestcover_30m.png", dpi=300, bbox_inches="tight")
print('figure saved to data/figures/hansen_remainingforestcover_30m.png')
plt.close(fig)