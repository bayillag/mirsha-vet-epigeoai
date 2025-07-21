import os
import sys
import psycopg2
import pandas as pd
import geopandas as gpd
from dotenv import load_dotenv
from sqlalchemy import create_engine
import zipfile

# --- Configuration ---
# Add the project's root directory to the Python path to allow imports from `src`
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.core.database import get_db_connection

# Define paths to data files
SCHEMA_SQL_PATH = "schema.sql"
CASES_CSV_PATH = "data/raw/cases/dovar_ii_cases.csv"
WOREDAS_ZIP_PATH = "data/raw/gis/south_omo_woredas.zip"

def execute_sql_from_file(conn, filepath):
    """Executes a SQL script file on the given database connection."""
    with open(filepath, 'r') as f:
        sql_script = f.read()
    with conn.cursor() as cur:
        cur.execute(sql_script)
    conn.commit()
    print(f"✅ SQL script '{filepath}' executed successfully.")

def populate_diseases_table(conn, cases_df):
    """Populates the 'diseases' table from the unique diseases in the cases CSV."""
    print("⏳ Populating 'diseases' table...")
    
    unique_diseases = cases_df[['disease_code', 'disease_name']].drop_duplicates().dropna()
    
    # In a real system, etiology would be mapped, here we use a placeholder
    unique_diseases['etiology'] = 'Unknown'
    
    with conn.cursor() as cur:
        for index, row in unique_diseases.iterrows():
            # Use ON CONFLICT DO NOTHING to prevent errors if a disease already exists
            cur.execute(
                """
                INSERT INTO diseases (disease_code, disease_name, etiology)
                VALUES (%s, %s, %s)
                ON CONFLICT (disease_code) DO NOTHING;
                """,
                (row['disease_code'], row['disease_name'], row['etiology'])
            )
    conn.commit()
    print(f"✅ 'diseases' table populated with {len(unique_diseases)} unique diseases.")

def populate_woredas_table(conn):
    """
    Unzips the shapefile and loads the woreda geometries and names into the database.
    Uses GeoPandas and SQLAlchemy for robust spatial data insertion.
    """
    print("⏳ Populating 'admin_woredas' table from shapefile...")

    if not os.path.exists(WOREDAS_ZIP_PATH):
        print(f"❌ ERROR: Woreda zip file not found at '{WOREDAS_ZIP_PATH}'")
        return
        
    # Unzip the shapefile
    unzip_dir = "data/raw/gis/temp_woreda_shapefile"
    with zipfile.ZipFile(WOREDAS_ZIP_PATH, 'r') as zip_ref:
        zip_ref.extractall(unzip_dir)
        
    shp_path = None
    for file in os.listdir(unzip_dir):
        if file.endswith('.shp'):
            shp_path = os.path.join(unzip_dir, file)
            break
            
    if not shp_path:
        print("❌ No .shp file found in the zip archive.")
        return

    # Load shapefile into a GeoDataFrame
    woredas_gdf = gpd.read_file(shp_path)
    
    # Standardize column names to match our schema (adjust as needed)
    # This is a common and crucial step
    woredas_gdf.rename(columns={
        'woreda_c': 'woreda_code',
        'woreda_n': 'woreda_name',
        'zone_n': 'zone_name',
        'region_n': 'region_name'
    }, inplace=True)
    
    # Ensure all required columns are present
    required_cols = ['woreda_code', 'woreda_name', 'geometry']
    if not all(col in woredas_gdf.columns for col in required_cols):
        print(f"❌ Shapefile is missing required columns. Needs: {required_cols}. Found: {woredas_gdf.columns.tolist()}")
        return

    # Create a SQLAlchemy engine for GeoPandas to use
    db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@db:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    engine = create_engine(db_url)
    
    # Use to_sql to insert the GeoDataFrame into the PostGIS table
    woredas_gdf[required_cols + ['zone_name', 'region_name']].to_sql(
        'admin_woredas',
        engine,
        if_exists='append', # Use 'append' as the table already exists
        index=False,
        dtype={'geom': 'geometry'}
    )
    print(f"✅ 'admin_woredas' table populated with {len(woredas_gdf)} geometries.")

def populate_outbreaks_table(conn, cases_df):
    """Populates the 'outbreaks' table with the initial report data."""
    print("⏳ Populating 'outbreaks' table with initial reports...")
    
    with conn.cursor() as cur:
        for index, row in cases_df.iterrows():
            cur.execute(
                """
                INSERT INTO outbreaks (report_date, woreda_code, latitude, longitude, species_affected, initial_complaint, reporter_name, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (
                    row['report_date'],
                    row['woreda_code'],
                    row['latitude'],
                    row['longitude'],
                    [row['species']], # Convert single species to an array
                    row['complaint'],
                    "Mock Data Generator",
                    "Unassigned" # All mock reports start as unassigned
                )
            )
    conn.commit()
    print(f"✅ 'outbreaks' table populated with {len(cases_df)} initial reports.")


def main():
    """Main function to orchestrate the database setup."""
    print("--- Mirsha VetEpiGeoAI Database Setup Script ---")
    load_dotenv()
    
    conn = get_db_connection()
    if not conn:
        print("❌ Halting. Could not establish database connection.")
        sys.exit(1)

    try:
        # Step 1: Create the database schema
        execute_sql_from_file(conn, SCHEMA_SQL_PATH)
        
        # Step 2: Load the source CSV data
        print(f"⏳ Reading source data from '{CASES_CSV_PATH}'...")
        if not os.path.exists(CASES_CSV_PATH):
            print(f"❌ ERROR: Cases CSV file not found at '{CASES_CSV_PATH}'. Run generate_mock_cases.py first.")
            return
        cases_df = pd.read_csv(CASES_CSV_PATH)
        print("✅ Source data loaded.")
        
        # Step 3: Populate the lookup tables first
        populate_diseases_table(conn, cases_df)
        populate_woredas_table(conn)
        
        # Step 4: Populate the main outbreaks table
        populate_outbreaks_table(conn, cases_df)

        print("\n🎉 Database setup complete! The platform is ready to be used.")

    except Exception as e:
        print(f"\n❌ An error occurred during database setup: {e}")
        conn.rollback() # Rollback any partial changes
    finally:
        if conn:
            conn.close()
            print("🔌 Database connection closed.")

if __name__ == "__main__":
    main()