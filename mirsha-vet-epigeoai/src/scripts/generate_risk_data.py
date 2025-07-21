import geopandas as gpd
import pandas as pd
import numpy as np
from src.core import database as db

def generate_and_save_risk_data():
    """
    Fetches woreda geometries and generates random, plausible risk factor data
    for demonstration purposes. Saves the result as a GeoPackage file.
    """
    print("⏳ Generating simulated risk factor data...")

    # Fetch woreda geometries from the database
    conn = db.get_db_connection()
    if not conn:
        print("❌ Could not connect to database. Halting.")
        return

    woredas_sql = "SELECT woreda_code, woreda_name, geom FROM admin_woredas;"
    woredas_gdf = gpd.read_postgis(woredas_sql, conn, geom_col='geom')
    conn.close()

    if woredas_gdf.empty:
        print("❌ Woredas table is empty. Please load administrative boundaries first.")
        return

    # --- Simulate Risk Factor Data ---
    num_woredas = len(woredas_gdf)
    np.random.seed(42) # for reproducibility

    # Normalize data to a 0-1 scale for easy weighting
    woredas_gdf['cattle_density'] = np.random.rand(num_woredas)
    woredas_gdf['proximity_to_market'] = np.random.rand(num_woredas) # Assume 0=very close, 1=far
    woredas_gdf['proximity_to_road'] = np.random.rand(num_woredas)
    woredas_gdf['rainfall_anomaly'] = np.random.uniform(-1, 1, num_woredas) # -1=dry, 1=wet
    woredas_gdf['vegetation_index'] = np.random.rand(num_woredas) # NDVI

    # --- Save to GeoPackage ---
    output_path = "data/external/risk_factors/woreda_risk_factors.gpkg"
    try:
        woredas_gdf.to_file(output_path, driver="GPKG")
        print(f"✅ Simulated risk factor data saved successfully to '{output_path}'")
    except Exception as e:
        print(f"❌ Error saving GeoPackage file: {e}")

if __name__ == "__main__":
    generate_and_save_risk_data()