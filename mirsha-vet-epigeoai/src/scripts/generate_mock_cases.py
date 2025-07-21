import pandas as pd
import numpy as np
import datetime
import os

# --- Configuration ---
# Adjust these parameters to customize the generated data
NUM_RECORDS = 1500
START_DATE = "2020-01-01"
END_DATE = "2023-12-31"
OUTPUT_DIR = "data/raw/cases"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "dovar_ii_cases.csv")

# --- Data Definitions (Based on Ethiopian Data Standard & Context) ---

# Define diseases with their codes and relative frequency
DISEASES = {
    "FMD": {"code": "01.01.02.21", "weight": 0.30},
    "PPR": {"code": "01.01.02.43", "weight": 0.25},
    "LSD": {"code": "01.01.02.31", "weight": 0.20},
    "Anthrax": {"code": "01.01.01.04", "weight": 0.10},
    "CBPP": {"code": "01.01.01.21", "weight": 0.10},
    "Rabies": {"code": "01.01.02.44", "weight": 0.05},
}

# Define woredas with codes, coordinates, and a "hotspot" factor
WOREDAS = {
    "Bena Tsemay": {"code": "ET_WR_001", "lat": 5.33, "lon": 36.75, "hotspot_factor": 3},
    "Dassenech":   {"code": "ET_WR_002", "lat": 4.88, "lon": 36.00, "hotspot_factor": 3},
    "Hamer":       {"code": "ET_WR_003", "lat": 5.10, "lon": 36.60, "hotspot_factor": 2},
    "Nyangatom":   {"code": "ET_WR_004", "lat": 5.25, "lon": 36.30, "hotspot_factor": 2},
    "Male":        {"code": "ET_WR_005", "lat": 5.60, "lon": 36.90, "hotspot_factor": 1},
    "Salamago":    {"code": "ET_WR_006", "lat": 5.80, "lon": 36.50, "hotspot_factor": 1},
}

SPECIES_DISEASE_MAP = {
    "FMD": ["Cattle", "Sheep", "Goats"],
    "PPR": ["Sheep", "Goats"],
    "LSD": ["Cattle"],
    "Anthrax": ["Cattle", "Sheep", "Goats", "Camels"],
    "CBPP": ["Cattle"],
    "Rabies": ["Cattle", "Dog", "Camel"] # Including Dog as a relevant species
}

def generate_mock_data():
    """Generates a realistic mock dataset for disease outbreaks."""
    
    print(f"🔥 Generating {NUM_RECORDS} mock outbreak records...")
    
    # Prepare lists and weights for random selection
    disease_names = list(DISEASES.keys())
    disease_weights = [d['weight'] for d in DISEASES.values()]
    
    woreda_names = list(WOREDAS.keys())
    woreda_weights = np.array([w['hotspot_factor'] for w in WOREDAS.values()])
    woreda_probabilities = woreda_weights / woreda_weights.sum()

    records = []
    
    # Generate random dates
    start_ts = pd.to_datetime(START_DATE).timestamp()
    end_ts = pd.to_datetime(END_DATE).timestamp()
    date_timestamps = np.random.randint(start_ts, end_ts, NUM_RECORDS)
    random_dates = [datetime.date.fromtimestamp(ts) for ts in date_timestamps]

    for i in range(NUM_RECORDS):
        # Select woreda and disease based on weights
        woreda_name = np.random.choice(woreda_names, p=woreda_probabilities)
        disease_name = np.random.choice(disease_names, p=disease_weights)
        
        # Select a plausible species for the chosen disease
        species = np.random.choice(SPECIES_DISEASE_MAP[disease_name])
        
        # Generate epidemiologically sound numbers
        total_susceptible = np.random.randint(20, 501)
        # Attack Rate between 1% and 40%
        attack_rate = np.random.uniform(0.01, 0.40)
        num_cases = max(1, int(total_susceptible * attack_rate))
        # Case Fatality Rate between 0% and 30%
        cfr = np.random.uniform(0.0, 0.30)
        deaths = int(num_cases * cfr)
        
        # Add random jitter to coordinates
        base_lat = WOREDAS[woreda_name]['lat']
        base_lon = WOREDAS[woreda_name]['lon']
        lat = base_lat + np.random.uniform(-0.05, 0.05)
        lon = base_lon + np.random.uniform(-0.05, 0.05)

        records.append({
            "report_date": random_dates[i],
            "disease_name": disease_name,
            "disease_code": DISEASES[disease_name]['code'],
            "woreda_name": woreda_name,
            "woreda_code": WOREDAS[woreda_name]['code'],
            "species": species,
            "total_susceptible": total_susceptible,
            "cases": num_cases,
            "deaths": deaths,
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "complaint": f"Initial field report for suspected {disease_name} in {species}."
        })

    # Create DataFrame and save
    df = pd.DataFrame(records)
    
    # Ensure directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Mock data generation complete. {len(df)} records saved to '{OUTPUT_FILE}'")

if __name__ == "__main__":
    generate_mock_data()