"""
Set up the working directory to create data/figures, 
data/hansen_gee_025deg, and data/hansen_gee_30m

"""

# Import packages
from pathlib import Path
 
# Define (sub)folders
folders = [
    "data",
    "data/figures",
    "data/hansen_gee_025deg",
    "data/hansen_gee_30m",
]
 
# Create folders if needed
for folder in folders:
    path = Path(folder)
    existed = path.exists()
    path.mkdir(parents=True, exist_ok=True)
    print(f"{'exists ' if existed else 'created'}: {path}")
 