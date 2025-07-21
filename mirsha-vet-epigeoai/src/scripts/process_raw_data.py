import os
import sys
import geopandas as gpd
import pandas as pd
import zipfile

# --- Configuration ---
# Ensure the script can find the 'src' directory for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Define input and output paths
RAW_CASES_PATH = "data/raw/cases/dovar_ii_cases.csv"
RAW_GIS_ZIP_PATH = "data/raw/gis/south_omo_woredas.zip"
PROCESSED_DIR = "data/processed"
PROCESSED_OUTPUT_PATH = os.path.join(PROCESSED_DIR, "woreda_summary.gpkg")

def process_data_pipeline():
    """
    Executes the full data processing pipeline:
    1. Loads raw case and spatial data.
    2. Aggregates case statistics by woreda.
    3. Merges statistics with woreda geometries.
    4. Calculates epidemiological rates.
    5. Saves the final analysis-ready GeoPackage file.
    """
    print("--- Starting Data Processing Pipeline ---")

    # --- Step 1: Load Raw Data ---
    print(f"⏳ Loading raw case data from '{RAW_CASES_PATH}'...")
    try:
        cases_df = pd.read_csv(RAW_CASES_PATH)
        cases_df['report_date'] = pd.to_datetime(cases_df['report_date'])
    except FileNotFoundError:
        print(f"❌ ERROR: Case data file not found. Please run 'generate_mock_cases.py' first.")
        sys.exit(1)

    print(f"⏳ Loading and unzipping spatial data from '{RAW_GIS_ZIP_PATH}'...")
    try:
        unzip_dir = "data/raw/gis/temp_unzipped_shapefile"
        with zipfile.ZipFile(RAW_GIS_ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(unzip_dir)
        
        shp_path = next((os.path.join(unzip_dir, f) for f in os.listdir(unzip_dir) if f.endswith('.shp')), None)
        woredas_gdf = gpd.read_file(shp_path)
    except (FileNotFoundError, StopIteration):
        print(f"❌ ERROR: Shapefile data not found. Please run 'generate_gis_data.py' first.")
        sys.exit(1)
        
    print("✅ Raw data loaded successfully.")

    # --- Step 2: Aggregate Case Data ---
    print("⏳ Aggregating outbreak statistics by woreda...")
    # Group by the woreda name from the case data to get total counts
    woreda_summary = cases_df.groupby('woreda_name').agg(
        total_cases=('cases', 'sum'),
        total_deaths=('deaths', 'sum'),
        total_susceptible=('total_susceptible', 'sum'),
        outbreak_count=('report_date', 'count') # Count the number of distinct reports
    ).reset_index()
    print("✅ Case data aggregated.")

    # --- Step 3: Merge Spatial and Tabular Data ---
    print("⏳ Merging aggregated statistics with woreda geometries...")
    # The generated shapefile uses 'woreda_n' as the name column
    analysis_gdf = woredas_gdf.merge(
        woreda_summary, 
        left_on='woreda_n', 
        right_on='woreda_name', 
        how='left'
    )
    
    # Clean up after merge
    analysis_gdf.drop(columns=['woreda_name'], inplace=True) # Drop redundant name column
    # Fill woredas with no reported outbreaks with 0
    fill_cols = ['total_cases', 'total_deaths', 'total_susceptible', 'outbreak_count']
    analysis_gdf[fill_cols] = analysis_gdf[fill_cols].fillna(0).astype(int)
    print("✅ Data merged successfully.")

    # --- Step 4: Calculate Derived Epidemiological Rates ---
    print("⏳ Calculating epidemiological rates...")
    
    # Calculate Attack Rate, handling division by zero
    analysis_gdf['attack_rate_percent'] = (
        (analysis_gdf['total_cases'] / analysis_gdf['total_susceptible']) * 100
    ).where(analysis_gdf['total_susceptible'] > 0, 0).round(2)
    
    # Calculate Case Fatality Rate, handling division by zero
    analysis_gdf['cfr_percent'] = (
        (analysis_gdf['total_deaths'] / analysis_gdf['total_cases']) * 100
    ).where(analysis_gdf['total_cases'] > 0, 0).round(2)
    
    print("✅ Rates calculated.")

    # --- Step 5: Save Processed Data ---
    print(f"⏳ Saving processed data to '{PROCESSED_OUTPUT_PATH}'...")
    
    # Ensure the output directory exists
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    try:
        analysis_gdf.to_file(PROCESSED_OUTPUT_PATH, driver="GPKG", layer="woreda_summary")
        print("🎉 Processing complete! Analysis-ready data is now available.")
    except Exception as e:
        print(f"❌ Failed to save GeoPackage file. Error: {e}")
        
    # --- Clean up unzipped files ---
    for f in os.listdir(unzip_dir):
        os.remove(os.path.join(unzip_dir, f))
    os.rmdir(unzip_dir)
    print("🗑️ Cleaned up temporary unzipped files.")


if __name__ == "__main__":
    # Ensure the script is run from the root of the project directory
    if not os.path.basename(os.getcwd()) == 'mirsha-vet-epigeoai':
        print("‼️  Please run this script from the root 'mirsha-vet-epigeoai' directory.")
    else:
        process_data_pipeline()