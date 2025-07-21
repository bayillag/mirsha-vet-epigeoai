import os
import psycopg2
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

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
