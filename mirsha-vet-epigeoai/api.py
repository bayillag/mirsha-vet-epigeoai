import os
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# --- Flask App Initialization ---
app = Flask(__name__)
load_dotenv()

# --- Database Connection Function (Independent of Streamlit) ---
def get_api_db_connection():
    """Establishes a direct connection to the database for the API."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST_API", "localhost"), # Use a different var for flexibility
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "vet_epigeoai_db"),
            user=os.getenv("DB_USER", "vet_user"),
            password=os.getenv("DB_PASSWORD", "strongpassword")
        )
        return conn
    except Exception as e:
        print(f"API Database connection error: {e}")
        return None

# --- API Security Middleware ---
@app.before_request
def check_api_key():
    """Checks for a valid API key before processing any request."""
    # Exclude the health check endpoint from authentication
    if request.endpoint == 'health_check':
        return

    api_key = request.headers.get('X-API-KEY')
    if not api_key:
        return jsonify({"error": "Missing API Key"}), 401
    
    conn = get_api_db_connection()
    if not conn:
        return jsonify({"error": "Database service unavailable"}), 503
        
    with conn.cursor() as cur:
        cur.execute("SELECT partner_name FROM api_keys WHERE api_key = %s AND is_active = TRUE", (api_key,))
        result = cur.fetchone()
    conn.close()

    if not result:
        return jsonify({"error": "Invalid or inactive API Key"}), 403
    
    # You could add more granular permission checks here in a real system
    # For example: check if result[0] has 'read:zoonotic_outbreaks' permission

# --- API Endpoints ---

@app.route("/")
def health_check():
    """A simple health check endpoint to confirm the API is running."""
    return jsonify({"status": "Mirsha VetEpiGeoAI API is running"}), 200

@app.route("/api/v1/zoonotic_outbreaks", methods=['GET'])
def get_zoonotic_outbreaks():
    """
    Returns a list of confirmed zoonotic outbreaks.
    Filters by date are possible with query parameters (e.g., ?start_date=YYYY-MM-DD)
    """
    start_date = request.args.get('start_date', '1900-01-01')
    
    # In a real system, you'd have a 'is_zoonotic' flag in your diseases table.
    # For now, we'll hardcode a list.
    ZOONOTIC_DISEASES = ['Anthrax', 'Rabies', 'Rift Valley Fever']
    
    conn = get_api_db_connection()
    if not conn:
        return jsonify({"error": "Database service unavailable"}), 503

    # Use a RealDictCursor to get results as dictionaries
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        sql = """
            SELECT 
                o.outbreak_id,
                d.disease_name,
                o.confirmation_date, -- Assumes a confirmation_date field exists
                a.woreda_name,
                ST_AsGeoJSON(a.geom) as geometry -- Serve geometry as GeoJSON
            FROM outbreaks o
            JOIN diseases d ON o.disease_code = d.disease_code
            JOIN admin_woredas a ON o.woreda_code = a.woreda_code
            WHERE o.status = 'Confirmed'
            AND d.disease_name = ANY(%s)
            AND o.confirmation_date >= %s;
        """
        cur.execute(sql, (ZOONOTIC_DISEASES, start_date))
        results = cur.fetchall()
        
        # Convert GeoJSON string to a proper JSON object
        for row in results:
            row['geometry'] = json.loads(row['geometry'])

    conn.close()
    return jsonify(results), 200


if __name__ == "__main__":
    # To run this API: open a NEW terminal in Codespaces and run `python api.py`
    app.run(host='0.0.0.0', port=5001, debug=True)