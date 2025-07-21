#!/bin/bash

# ==============================================================================
# Bash Script to Create the Mirsha VetEpiGeoAI Analysis Notebook
# ==============================================================================

# --- Configuration ---
NOTEBOOK_DIR="notebooks"
NOTEBOOK_FILE="$NOTEBOOK_DIR/Mirsha_VetEpiGeoAI_Analysis.ipynb"

# --- Main Execution ---
echo "📝 Creating the analysis notebook..."

# 1. Create the notebooks directory if it doesn't exist
mkdir -p "$NOTEBOOK_DIR"
echo "✅ Directory '$NOTEBOOK_DIR' is ready."

# 2. Write the entire JSON content to the .ipynb file using a heredoc
cat > "$NOTEBOOK_FILE" << 'EOF'
{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Mirsha VetEpiGeoAI: Interactive Analysis Notebook\n\nThis Google Colab notebook provides a detailed, step-by-step walkthrough of the data processing, spatial analysis, and visualization for the Mirsha VetEpiGeoAI project. It is designed for researchers, analysts, and collaborators who wish to understand the methodology behind the findings.\n\n**This notebook is one part of a larger ecosystem:**\n*   **This Report (Colab):** For deep, reproducible analysis.\n*   **Operational Dashboard (Web App):** For real-time, user-friendly decision support. You can launch the dashboard from our main [GitHub Repository](https://github.com/bayillag/mirsha-vet-epigeoai).\n\nThis notebook clones the main repository to ensure it is always working with the most up-to-date data and code."
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Step 1: Install Libraries and Clone Repository"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "print(\"⏳ Installing required libraries...\")\n!pip install -q geopandas pysal folium mapclassify\nprint(\"✅ Libraries installed successfully.\")\n\n# Import all necessary modules\nimport pandas as pd\nimport geopandas as gpd\nimport folium\nimport zipfile\nimport os\nimport pysal.lib\nimport esda\nimport numpy as np\nimport matplotlib.pyplot as plt\n\n# Clone the GitHub Repository to access data directly\nREPO_URL = \"https://github.com/bayillag/mirsha-vet-epigeoai.git\"\nREPO_NAME = \"mirsha-vet-epigeoai\"\n\nif os.path.exists(REPO_NAME):\n    print(\"✅ Repository already cloned.\")\nelse:\n    print(f\"⏳ Cloning repository: {REPO_URL}\")\n    !git clone -q {REPO_URL}\n    print(\"✅ Repository cloned successfully.\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Step 2: Load and Prepare Data\n\nWe will now load the spatial data (woreda boundaries) and the tabular data (mock disease cases) from the cloned repository and merge them into a single GeoDataFrame."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "print(\"⏳ Loading and preparing data...\")\n\n# Define paths based on the cloned repository structure\nshapefile_zip_path = f\"{REPO_NAME}/data/raw/gis/south_omo_woredas.zip\"\ncases_csv_path = f\"{REPO_NAME}/data/raw/cases/dovar_ii_cases.csv\"\noutput_dir = 'shapefile_data'\n\n# Unzip the shapefile\nwith zipfile.ZipFile(shapefile_zip_path, 'r') as zip_ref:\n    zip_ref.extractall(output_dir)\n\n# Find the .shp file path\nshp_path = next((os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith('.shp')), None)\n\n# Load spatial and tabular data\nworedas_gdf = gpd.read_file(shp_path)\ncases_df = pd.read_csv(cases_csv_path)\ncases_df['report_date'] = pd.to_datetime(cases_df['report_date'])\n\n# Aggregate case data by woreda\nworeda_summary = cases_df.groupby('woreda_name').agg(\n    total_cases=('cases', 'sum'),\n    total_deaths=('deaths', 'sum'),\n    total_susceptible=('total_susceptible', 'sum')\n).reset_index()\n\n# Merge aggregated data with geometries\nanalysis_gdf = woredas_gdf.merge(woreda_summary, left_on='woreda_n', right_on='woreda_name', how='left')\nanalysis_gdf[['total_cases', 'total_deaths', 'total_susceptible']] = analysis_gdf[['total_cases', 'total_deaths', 'total_susceptible']].fillna(0)\n\n# Calculate rates for analysis\nanalysis_gdf['attack_rate'] = (analysis_gdf['total_cases'] / analysis_gdf['total_susceptible']).where(analysis_gdf['total_susceptible'] > 0, 0)\nanalysis_gdf['cfr'] = (analysis_gdf['total_deaths'] / analysis_gdf['total_cases']).where(analysis_gdf['total_cases'] > 0, 0)\n\nprint(\"✅ Data loaded and prepared for analysis.\")\nanalysis_gdf.head()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Step 3: Exploratory Spatial Data Analysis (ESDA)\n\nNow we'll create a choropleth map to visualize the spatial distribution of the total number of cases. This helps us get an initial 'feel' for the data and identify potential areas of high concentration."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "print(\"Visualizing Total Cases per Woreda...\")\n\n# Create an interactive map with Folium\nmap_center = [analysis_gdf.unary_union.centroid.y, analysis_gdf.unary_union.centroid.x]\nm = folium.Map(location=map_center, zoom_start=8, tiles=\"CartoDB positron\")\n\nfolium.Choropleth(\n    geo_data=analysis_gdf,\n    data=analysis_gdf,\n    columns=['woreda_n', 'total_cases'],\n    key_on='feature.properties.woreda_n',\n    fill_color='YlOrRd',\n    fill_opacity=0.7,\n    line_opacity=0.2,\n    legend_name='Total Reported Cases'\n).add_to(m)\n\n# Display the map\nm"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Step 4: Hotspot Analysis (Local Moran's I)\n\nVisual inspection is useful, but not statistically rigorous. We will now perform a Local Moran's I (LISA) analysis to identify statistically significant spatial clusters (hotspots and coldspots) of disease cases."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "print(\"⏳ Performing Local Moran's I (LISA) analysis...\")\n\n# Create spatial weights matrix (Queen contiguity)\nw = pysal.lib.weights.Queen.from_dataframe(analysis_gdf)\nw.transform = 'r' # Row-standardize\n\n# Calculate Local Moran's I\nlisa = esda.Moran_Local(analysis_gdf['total_cases'], w)\n\n# Add results to our GeoDataFrame\nanalysis_gdf['lisa_q'] = lisa.q\nanalysis_gdf['lisa_p'] = lisa.p_sim\n\ncluster_labels = {\n    1: 'High-High (Hotspot)', 2: 'Low-High (Doughnut)',\n    3: 'Low-Low (Coldspot)', 4: 'High-Low (Diamond)'\n}\nanalysis_gdf['cluster_type'] = analysis_gdf['lisa_q'].map(cluster_labels)\nanalysis_gdf.loc[analysis_gdf['lisa_p'] > 0.05, 'cluster_type'] = 'Not Significant'\n\nprint(\"✅ LISA analysis complete.\")\nprint(\"Significant Clusters Found:\")\nanalysis_gdf[analysis_gdf['lisa_p'] <= 0.05][['woreda_name', 'total_cases', 'cluster_type']]"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Step 5: Visualize Hotspots\n\nFinally, we map the results of the LISA analysis to clearly show the locations of the statistically significant clusters."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "print(\"Visualizing Hotspot and Coldspot Clusters...\")\n\nm2 = folium.Map(location=map_center, zoom_start=8, tiles=\"CartoDB positron\")\n\n# Define colors for cluster types\ncluster_colors = {\n    'High-High (Hotspot)': 'red',\n    'Low-Low (Coldspot)': 'blue',\n    'High-Low (Diamond)': 'orange',\n    'Low-High (Doughnut)': 'yellow',\n    'Not Significant': 'lightgray'\n}\n\n# Add styled GeoJSON layer for the LISA results\nfolium.GeoJson(\n    analysis_gdf,\n    style_function=lambda feature: {\n        'fillColor': cluster_colors.get(feature['properties']['cluster_type'], 'gray'),\n        'color': 'black',\n        'weight': 0.5,\n        'fillOpacity': 0.7 if feature['properties']['cluster_type'] != 'Not Significant' else 0.2\n    },\n    tooltip=folium.GeoJsonTooltip(fields=['woreda_name', 'total_cases', 'cluster_type']),\n    name='LISA Clusters'\n).add_to(m2)\n\nm2"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "name": "python",
   "version": "3.10.12"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}
EOF

echo "✅ Notebook file '$NOTEBOOK_FILE' created successfully."