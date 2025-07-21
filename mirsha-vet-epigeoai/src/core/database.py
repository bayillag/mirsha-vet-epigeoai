import os
import psycopg2
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import json 
import geopandas as gpd

# Load environment variables from a .env file
load_dotenv()

# Use Streamlit's connection management for efficiency
@st.cache_resource
def get_db_connection():
    """
    Establishes a connection to the PostgreSQL database using credentials
    from environment variables. Uses Streamlit's caching to maintain a
    singleton connection.
    """
    try:
        conn = psycopg2.connect(
            host="db", # In Docker Compose, 'db' is the hostname for the database service
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "vet_epigeoai_db"),
            user=os.getenv("DB_USER", "vet_user"),
            password=os.getenv("DB_PASSWORD", "strongpassword")
        )
        print("Database connection established.")
        return conn
    except psycopg2.OperationalError as e:
        st.error(f"❌ Database connection failed. Is the database service running? Details: {e}")
        return None

def add_new_outbreak_report(reporter_name, woreda_name, lat, lon, species, complaint, report_date):
    """Inserts a new suspected outbreak report into the database."""
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection is not available."

    try:
        with conn.cursor() as cur:
            # First, find the woreda_code based on the woreda_name
            # NOTE: In a real system, you'd want fuzzy matching or a dropdown.
            cur.execute("SELECT woreda_code FROM admin_woredas WHERE woreda_name = %s", (woreda_name,))
            result = cur.fetchone()
            woreda_code = result[0] if result else None

            if not woreda_code:
                return False, f"Woreda '{woreda_name}' not found in database."

            sql = """
                INSERT INTO outbreaks (reporter_name, woreda_code, latitude, longitude, species_affected, initial_complaint, report_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING outbreak_id;
            """
            cur.execute(sql, (reporter_name, woreda_code, lat, lon, species, complaint, report_date))
            new_id = cur.fetchone()[0]
            conn.commit()
            return True, f"Report successfully submitted with Outbreak ID: {new_id}"
    except Exception as e:
        conn.rollback()
        return False, f"Database error: {e}"

def get_unassigned_reports():
    """Fetches all outbreak reports with the status 'Unassigned'."""
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame() # Return empty dataframe on connection failure

    sql = """
        SELECT o.outbreak_id, o.report_date, a.woreda_name, o.species_affected, o.initial_complaint
        FROM outbreaks o
        JOIN admin_woredas a ON o.woreda_code = a.woreda_code
        WHERE o.status = 'Unassigned'
        ORDER BY o.report_date DESC;
    """
    try:
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        st.error(f"Error fetching reports: {e}")
        return pd.DataFrame()

def assign_investigator_to_outbreak(outbreak_id, investigator_name):
    """Updates an outbreak's status to 'Assigned' and sets the investigator."""
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection is not available."
    
    sql = """
        UPDATE outbreaks
        SET investigator_name = %s, status = 'Assigned'
        WHERE outbreak_id = %s;
    """
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (investigator_name, outbreak_id))
            conn.commit()
        return True, f"Outbreak {outbreak_id} assigned to {investigator_name}."
    except Exception as e:
        conn.rollback()
        return False, f"Database error: {e}"
 

# ... (keep the existing functions: get_db_connection, add_new_outbreak_report, etc.) ...

def get_assigned_outbreaks(investigator_name):
    """Fetches outbreaks assigned to a specific investigator that are not yet completed."""
    conn = get_db_connection()
    if not conn: return pd.DataFrame()
    
    sql = """
        SELECT o.outbreak_id, o.report_date, a.woreda_name, o.initial_complaint
        FROM outbreaks o
        JOIN admin_woredas a ON o.woreda_code = a.woreda_code
        WHERE o.investigator_name = %s AND o.status = 'Assigned'
        ORDER BY o.report_date;
    """
    try:
        df = pd.read_sql(sql, conn, params=(investigator_name,))
        return df
    except Exception as e:
        st.error(f"Error fetching assigned outbreaks: {e}")
        return pd.DataFrame()

def get_outbreak_details(outbreak_id):
    """Fetches the initial report details for a specific outbreak ID."""
    conn = get_db_connection()
    if not conn: return None

    sql = """
        SELECT o.outbreak_id, o.report_date, a.woreda_name, o.species_affected, o.initial_complaint, o.reporter_name
        FROM outbreaks o
        JOIN admin_woredas a ON o.woreda_code = a.woreda_code
        WHERE o.outbreak_id = %s;
    """
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (outbreak_id,))
            result = cur.fetchone()
            if result:
                # Return as a dictionary for easy access
                return {
                    "id": result[0], "date": result[1], "woreda": result[2],
                    "species": result[3], "complaint": result[4], "reporter": result[5]
                }
            return None
    except Exception as e:
        st.error(f"Error fetching outbreak details: {e}")
        return None

def submit_full_investigation(outbreak_id, investigation_date, form_data, line_list_df, samples_df):
    """
    Submits the full investigation report, including form data, line list, and samples.
    This runs as a single database transaction.
    """
    conn = get_db_connection()
    if not conn: return False, "Database connection is not available."

    try:
        with conn.cursor() as cur:
            # 1. Update the main outbreaks table
            form_data_json = json.dumps(form_data)
            update_sql = """
                UPDATE outbreaks
                SET investigation_date = %s, form_data = %s, status = 'Completed'
                WHERE outbreak_id = %s;
            """
            cur.execute(update_sql, (investigation_date, form_data_json, outbreak_id))

            # 2. Insert line list data (if any)
            if not line_list_df.empty:
                for index, row in line_list_df.iterrows():
                    insert_case_sql = """
                        INSERT INTO outbreak_cases (outbreak_id, species, total_susceptible, cases, deaths, observation_date)
                        VALUES (%s, %s, %s, %s, %s, %s);
                    """
                    cur.execute(insert_case_sql, (outbreak_id, row['Species'], row['Susceptible'], row['Cases'], row['Deaths'], row['Date']))
            
            # 3. Insert sample data (if any)
            if not samples_df.empty:
                for index, row in samples_df.iterrows():
                    insert_sample_sql = """
                        INSERT INTO samples (outbreak_id, field_sample_id, sample_type, laboratory, submission_date)
                        VALUES (%s, %s, %s, %s, %s);
                    """
                    cur.execute(insert_sample_sql, (outbreak_id, row['Field ID'], row['Sample Type'], row['Laboratory'], row['Submission Date']))

            conn.commit()
            return True, f"Full investigation for Outbreak ID {outbreak_id} has been successfully submitted."

    except Exception as e:
        conn.rollback()
        return False, f"Database transaction failed: {e}"   

# ... (keep all existing functions) ...

def get_outbreaks_for_tracing():
    """Fetches confirmed or in-progress outbreaks that may need tracing."""
    conn = get_db_connection()
    if not conn: return pd.DataFrame()

    sql = """
        SELECT o.outbreak_id, o.investigation_date, d.disease_name, a.woreda_name
        FROM outbreaks o
        JOIN diseases d ON o.disease_code = d.disease_code
        JOIN admin_woredas a ON o.woreda_code = a.woreda_code
        WHERE o.status IN ('In Progress', 'Completed', 'Confirmed')
        ORDER BY o.investigation_date DESC;
    """
    try:
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        st.error(f"Error fetching outbreaks for tracing: {e}")
        return pd.DataFrame()

def get_tracing_links(outbreak_id):
    """Fetches all existing contact tracing links for a given outbreak ID."""
    conn = get_db_connection()
    if not conn: return pd.DataFrame()

    sql = "SELECT * FROM contact_tracing_links WHERE source_outbreak_id = %s;"
    try:
        df = pd.read_sql(sql, conn, params=(outbreak_id,))
        return df
    except Exception as e:
        st.error(f"Error fetching tracing links: {e}")
        return pd.DataFrame()

def add_tracing_link(source_outbreak_id, name, loc_type, lat, lon, date, contact_type, direction, notes):
    """Adds a new contact tracing link to the database."""
    conn = get_db_connection()
    if not conn: return False, "Database connection not available."

    sql = """
        INSERT INTO contact_tracing_links 
        (source_outbreak_id, linked_location_name, linked_location_type, latitude, longitude, contact_date, contact_type, direction, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (source_outbreak_id, name, loc_type, lat, lon, date, contact_type, direction, notes))
            conn.commit()
        return True, "Contact link added successfully."
    except Exception as e:
        conn.rollback()
        return False, f"Database error: {e}"
    
# ... (keep all existing functions) ...

@st.cache_data(ttl=600) # Cache the data for 10 minutes to avoid constant DB calls
def get_dashboard_data():
    """
    Fetches all completed/confirmed outbreaks and merges them with woreda geometries.
    Also aggregates case statistics for each woreda.
    """
    conn = get_db_connection()
    if not conn:
        return gpd.GeoDataFrame()

    # SQL query to fetch outbreak data and join with disease and woreda names
    outbreak_sql = """
        SELECT 
            o.outbreak_id,
            o.report_date,
            o.investigation_date,
            o.latitude,
            o.longitude,
            d.disease_name,
            a.woreda_name,
            a.woreda_code
        FROM outbreaks o
        LEFT JOIN diseases d ON o.disease_code = d.disease_code
        LEFT JOIN admin_woredas a ON o.woreda_code = a.woreda_code
        WHERE o.status IN ('Completed', 'Confirmed');
    """

    # SQL query to fetch aggregated case data
    cases_sql = """
        SELECT 
            o.woreda_code,
            d.disease_name,
            SUM(oc.cases) as total_cases,
            SUM(oc.deaths) as total_deaths,
            SUM(oc.total_susceptible) as total_susceptible
        FROM outbreak_cases oc
        JOIN outbreaks o ON oc.outbreak_id = o.outbreak_id
        JOIN diseases d ON o.disease_code = d.disease_code
        WHERE o.status IN ('Completed', 'Confirmed')
        GROUP BY o.woreda_code, d.disease_name;
    """
    
    # SQL query to fetch woreda geometries
    woreda_sql = "SELECT woreda_code, woreda_name, geom FROM admin_woredas;"

    try:
        outbreaks_df = pd.read_sql(outbreak_sql, conn)
        cases_df = pd.read_sql(cases_sql, conn)
        woredas_gdf = gpd.read_postgis(woreda_sql, conn, geom_col='geom', crs="EPSG:4326")

        # Merge the aggregated case data into the woreda GeoDataFrame
        dashboard_gdf = woredas_gdf.merge(cases_df, on='woreda_code', how='left')
        
        # Calculate Attack Rate and Case Fatality Rate
        # Avoid division by zero
        dashboard_gdf['attack_rate_percent'] = (
            (dashboard_gdf['total_cases'] / dashboard_gdf['total_susceptible']) * 100
        ).where(dashboard_gdf['total_susceptible'] > 0, 0)
        
        dashboard_gdf['cfr_percent'] = (
            (dashboard_gdf['total_deaths'] / dashboard_gdf['total_cases']) * 100
        ).where(dashboard_gdf['total_cases'] > 0, 0)

        # Fill NaNs for woredas with no cases
        dashboard_gdf[['total_cases', 'total_deaths', 'attack_rate_percent', 'cfr_percent']] = dashboard_gdf[['total_cases', 'total_deaths', 'attack_rate_percent', 'cfr_percent']].fillna(0)

        # Convert point data to a GeoDataFrame
        outbreaks_gdf = gpd.GeoDataFrame(
            outbreaks_df, 
            geometry=gpd.points_from_xy(outbreaks_df.longitude, outbreaks_df.latitude),
            crs="EPSG:4326"
        )
        
        print("✅ Dashboard data fetched and processed successfully.")
        return dashboard_gdf, outbreaks_gdf

    except Exception as e:
        st.error(f"Error building dashboard data: {e}")
        return gpd.GeoDataFrame(), gpd.GeoDataFrame()
    
  # ... (keep all existing functions) ...

def save_pe_session_results(outbreak_id, woreda_code, session_date, facilitator, method, data_payload):
    """Saves the results of a PE session (as a JSON object) to the database."""
    conn = get_db_connection()
    if not conn: return False, "Database connection not available."

    # Convert the Python dictionary to a JSON string for storing in JSONB
    session_data_json = json.dumps(data_payload)
    
    sql = """
        INSERT INTO pe_sessions 
        (outbreak_id, woreda_code, session_date, facilitator_name, pe_method, session_data)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING session_id;
    """
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (outbreak_id, woreda_code, session_date, facilitator, method, session_data_json))
            new_id = cur.fetchone()[0]
            conn.commit()
        return True, f"PE Session (ID: {new_id}) saved successfully."
    except Exception as e:
        conn.rollback()
        return False, f"Database error while saving PE session: {e}"  
    
# ... (keep all existing functions) ...

def get_all_samples():
    """Fetches all samples from the database for the tracking dashboard."""
    conn = get_db_connection()
    if not conn: return pd.DataFrame()
    
    sql = """
        SELECT 
            s.sample_id,
            s.field_sample_id,
            s.outbreak_id,
            a.woreda_name,
            s.sample_type,
            s.laboratory,
            s.submission_date,
            s.status,
            s.result,
            s.result_details,
            s.result_date
        FROM samples s
        LEFT JOIN outbreaks o ON s.outbreak_id = o.outbreak_id
        LEFT JOIN admin_woredas a ON o.woreda_code = a.woreda_code
        ORDER BY s.submission_date DESC;
    """
    try:
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        st.error(f"Error fetching sample data: {e}")
        return pd.DataFrame()

def get_sample_by_field_id(field_sample_id):
    """Fetches a single sample's details by its unique field ID."""
    conn = get_db_connection()
    if not conn: return None

    sql = "SELECT sample_id, field_sample_id, outbreak_id, status FROM samples WHERE field_sample_id = %s;"
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (field_sample_id,))
            result = cur.fetchone()
            if result:
                return {"id": result[0], "field_id": result[1], "outbreak_id": result[2], "status": result[3]}
            return None
    except Exception as e:
        st.error(f"Error fetching sample by field ID: {e}")
        return None

def update_sample_status(sample_id, new_status):
    """Updates the status of a sample (e.g., to 'In Transit', 'Received')."""
    conn = get_db_connection()
    if not conn: return False, "Database connection failed."
    
    sql = "UPDATE samples SET status = %s WHERE sample_id = %s;"
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (new_status, sample_id))
            conn.commit()
        return True, f"Status for sample {sample_id} updated to '{new_status}'."
    except Exception as e:
        conn.rollback()
        return False, f"Database error: {e}"

def submit_lab_result(sample_id, outbreak_id, result, result_details, result_date):
    """
    Submits a final laboratory result for a sample and updates the
    corresponding outbreak status to 'Confirmed' if the result is positive.
    """
    conn = get_db_connection()
    if not conn: return False, "Database connection failed."

    try:
        with conn.cursor() as cur:
            # 1. Update the samples table with the result
            sample_sql = """
                UPDATE samples 
                SET status = 'Results Available', result = %s, result_details = %s, result_date = %s
                WHERE sample_id = %s;
            """
            cur.execute(sample_sql, (result, result_details, result_date, sample_id))

            # 2. If the result is positive, update the parent outbreak's status
            if result.lower() == 'positive' and outbreak_id is not None:
                outbreak_sql = """
                    UPDATE outbreaks
                    SET status = 'Confirmed'
                    WHERE outbreak_id = %s;
                """
                cur.execute(outbreak_sql, (outbreak_id,))
            
            conn.commit()
        return True, f"Result for sample {sample_id} submitted successfully."
    except Exception as e:
        conn.rollback()
        return False, f"Database transaction failed: {e}"
    
# ... (keep all existing functions) ...

@st.cache_data(ttl=3600) # Cache for 1 hour
def get_surveillance_performance_data():
    """
    Fetches and calculates key performance indicators for the surveillance system.
    """
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame(), None

    # Query to calculate reporting timeliness and count reports per woreda
    sql = """
        SELECT 
            a.woreda_name,
            a.region_name,
            COUNT(o.outbreak_id) as total_reports,
            AVG(o.investigation_date - o.report_date) as avg_response_days
        FROM outbreaks o
        JOIN admin_woredas a ON o.woreda_code = a.woreda_code
        WHERE o.investigation_date IS NOT NULL
        GROUP BY a.woreda_name, a.region_name;
    """
    try:
        performance_df = pd.read_sql(sql, conn)
        
        # Calculate national averages
        national_avg_response = performance_df['avg_response_days'].mean().days if not performance_df.empty else 0
        
        return performance_df, national_avg_response
    except Exception as e:
        st.error(f"Error fetching performance data: {e}")
        return pd.DataFrame(), None

def get_historical_hotspots(disease_name):
    """
    Fetches aggregated case data for a specific disease to be used in
    risk-based survey planning.
    """
    conn = get_db_connection()
    if not conn:
        return gpd.GeoDataFrame()

    sql = """
        SELECT 
            a.woreda_code,
            a.woreda_name,
            a.geom,
            COALESCE(SUM(oc.cases), 0) as total_cases
        FROM admin_woredas a
        LEFT JOIN outbreaks o ON a.woreda_code = o.woreda_code AND o.status IN ('Completed', 'Confirmed')
        LEFT JOIN diseases d ON o.disease_code = d.disease_code AND d.disease_name = %(disease)s
        LEFT JOIN outbreak_cases oc ON o.outbreak_id = oc.outbreak_id
        GROUP BY a.woreda_code, a.woreda_name, a.geom;
    """
    try:
        gdf = gpd.read_postgis(sql, conn, geom_col='geom', params={'disease': disease_name})
        return gdf
    except Exception as e:
        st.error(f"Error fetching historical hotspot data: {e}")
        return gpd.GeoDataFrame()

# ... (keep all existing functions) ...

# === Functions for Resource Management (Module 10) ===

def get_inventory_data():
    """Fetches the complete inventory of all veterinary supplies."""
    conn = get_db_connection()
    if not conn: return pd.DataFrame()
    sql = "SELECT * FROM inventory ORDER BY location, item_type;"
    try:
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        st.error(f"Error fetching inventory data: {e}")
        return pd.DataFrame()

def get_personnel_data():
    """Fetches the complete roster of all veterinary personnel."""
    conn = get_db_connection()
    if not conn: return pd.DataFrame()
    sql = "SELECT * FROM personnel ORDER BY current_station, full_name;"
    try:
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        st.error(f"Error fetching personnel data: {e}")
        return pd.DataFrame()

def update_inventory_item(item_id, new_quantity):
    """Updates the quantity of a specific inventory item."""
    conn = get_db_connection()
    if not conn: return False, "Database connection failed."
    sql = "UPDATE inventory SET quantity = %s, last_updated = NOW() WHERE item_id = %s;"
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (new_quantity, item_id))
            conn.commit()
        return True, "Inventory updated successfully."
    except Exception as e:
        conn.rollback()
        return False, f"Database error: {e}"

def update_personnel_status(personnel_id, new_status):
    """Updates the status of a personnel member (e.g., to 'Deployed')."""
    conn = get_db_connection()
    if not conn: return False, "Database connection failed."
    sql = "UPDATE personnel SET status = %s WHERE personnel_id = %s;"
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (new_status, personnel_id))
            conn.commit()
        return True, "Personnel status updated."
    except Exception as e:
        conn.rollback()
        return False, f"Database error: {e}"

# ... (keep all existing functions) ...

def get_cases_for_outbreak(outbreak_id):
    """Fetches the detailed case line list for a single outbreak."""
    conn = get_db_connection()
    if not conn: return pd.DataFrame()
    sql = "SELECT * FROM outbreak_cases WHERE outbreak_id = %s;"
    try:
        df = pd.read_sql(sql, conn, params=(outbreak_id,))
        return df
    except Exception as e:
        st.error(f"Error fetching case data for outbreak {outbreak_id}: {e}")
        return pd.DataFrame()

# ... (keep all existing functions) ...

# === Functions for Market Chain Analysis (Module 13) ===
@st.cache_data(ttl=3600) # Cache for 1 hour
def get_movement_network_data(start_date, end_date, species):
    """
    Fetches aggregated livestock movement data to build a network graph.
    """
    conn = get_db_connection()
    if not conn: return pd.DataFrame()

    # This query aggregates all movements between two locations within the date range
    # It joins the locations table to get names and coordinates
    sql = """
        SELECT 
            orig.location_name as origin_name,
            orig.latitude as origin_lat,
            orig.longitude as origin_lon,
            dest.location_name as destination_name,
            dest.latitude as destination_lat,
            dest.longitude as destination_lon,
            SUM(m.num_animals) as total_animals
        FROM movements m
        JOIN locations orig ON m.origin_location_id = orig.location_id
        JOIN locations dest ON m.destination_location_id = dest.location_id
        WHERE m.movement_date BETWEEN %(start)s AND %(end)s
        AND (m.species = %(species)s OR %(species)s = 'All')
        GROUP BY orig.location_name, dest.location_name, 
                 orig.latitude, orig.longitude, dest.latitude, dest.longitude
        HAVING SUM(m.num_animals) > 0;
    """
    params = {'start': start_date, 'end': end_date, 'species': species}
    
    try:
        df = pd.read_sql(sql, conn, params=params)
        print(f"Fetched {len(df)} aggregated movement links.")
        return df
    except Exception as e:
        st.error(f"Error fetching movement network data: {e}")
        return pd.DataFrame()

# ... (keep all existing functions) ...

# === Functions for Molecular Surveillance (Module 14) ===
@st.cache_data(ttl=3600)
def get_molecular_surveillance_data():
    """
    Fetches a combined dataset of outbreaks, samples, and molecular data
    for genomic surveillance analysis.
    """
    conn = get_db_connection()
    if not conn: return pd.DataFrame()

    sql = """
        SELECT
            o.outbreak_id,
            o.investigation_date,
            a.woreda_name,
            o.latitude,
            o.longitude,
            d.disease_name,
            s.field_sample_id,
            s.result_details,
            md.serotype,
            md.genotype,
            md.sequence_data,
            md.phylogenetic_tree_newick
        FROM outbreaks o
        JOIN samples s ON o.outbreak_id = s.outbreak_id
        JOIN molecular_data md ON s.sample_id = md.sample_id
        JOIN diseases d ON o.disease_code = d.disease_code
        JOIN admin_woredas a ON o.woreda_code = a.woreda_code
        WHERE o.status = 'Confirmed' AND md.serotype IS NOT NULL;
    """
    try:
        df = pd.read_sql(sql, conn)
        print(f"Fetched {len(df)} records with molecular data.")
        return df
    except Exception as e:
        st.error(f"Error fetching molecular data: {e}")
        return pd.DataFrame()

# ... (keep all existing functions) ...

# === Functions for Communications (Module 15) ===

def log_communication_activity(outbreak_id, activity_type, audience, message, date, officer):
    """Logs a communication or engagement activity to the database."""
    conn = get_db_connection()
    if not conn: return False, "Database connection failed."

    sql = """
        INSERT INTO communications_log (outbreak_id, activity_type, target_audience, message_content, communication_date, officer_name)
        VALUES (%s, %s, %s, %s, %s, %s);
    """
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (outbreak_id, activity_type, audience, message, date, officer))
            conn.commit()
        return True, "Communication activity logged successfully."
    except Exception as e:
        conn.rollback()
        return False, f"Database error: {e}"

@st.cache_data(ttl=300) # Cache for 5 minutes
def get_public_outbreak_map_data():
    """
    Fetches only the essential, non-sensitive data for the public-facing map.
    Only shows woreda-level locations for confirmed outbreaks.
    """
    conn = get_db_connection()
    if not conn: return gpd.GeoDataFrame()

    sql = """
        SELECT
            o.outbreak_id,
            d.disease_name,
            o.confirmation_date,
            a.woreda_name,
            a.geom
        FROM outbreaks o
        JOIN diseases d ON o.disease_code = d.disease_code
        JOIN admin_woredas a ON o.woreda_code = a.woreda_code
        WHERE o.status = 'Confirmed';
    """
    try:
        gdf = gpd.read_postgis(sql, conn, geom_col='geom')
        return gdf
    except Exception as e:
        st.error(f"Error fetching public map data: {e}")
        return gpd.GeoDataFrame()

