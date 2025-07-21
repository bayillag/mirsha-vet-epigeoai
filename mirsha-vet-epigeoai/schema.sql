-- Creates the database schema for Mirsha VetEpiGeoAI
-- Compliant with the Ethiopian National Livestock Data Standard

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Drop existing tables for a clean setup
DROP TABLE IF EXISTS samples CASCADE;
DROP TABLE IF EXISTS outbreak_cases CASCADE;
DROP TABLE IF EXISTS outbreaks CASCADE;
DROP TABLE IF EXISTS diseases CASCADE;
DROP TABLE IF EXISTS admin_woredas CASCADE;

-- Table for administrative boundaries
CREATE TABLE admin_woredas (
    woreda_code VARCHAR(20) PRIMARY KEY,
    woreda_name VARCHAR(100) NOT NULL UNIQUE,
    zone_name VARCHAR(100),
    region_name VARCHAR(100),
    geom GEOMETRY(MultiPolygon, 4326)
);
CREATE INDEX woredas_geom_idx ON admin_woredas USING GIST (geom);

-- Table for disease definitions
CREATE TABLE diseases (
    disease_code VARCHAR(20) PRIMARY KEY,
    disease_name VARCHAR(255) NOT NULL UNIQUE,
    etiology VARCHAR(50)
);

-- Main table for outbreak investigation reports
CREATE TABLE outbreaks (
    outbreak_id SERIAL PRIMARY KEY,
    report_date DATE NOT NULL,
    woreda_code VARCHAR(20) REFERENCES admin_woredas(woreda_code),
    latitude DECIMAL(9, 6),
    longitude DECIMAL(9, 6),
    species_affected TEXT[],
    initial_complaint TEXT NOT NULL,
    reporter_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'Unassigned', -- Unassigned, Assigned, In Progress, Completed, Resolved
    investigator_name VARCHAR(255),
    investigation_date DATE,
    form_data JSONB, -- Flexible field for all other investigation form data
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table for line-listing of cases within an outbreak
CREATE TABLE outbreak_cases (
    case_id SERIAL PRIMARY KEY,
    outbreak_id INTEGER REFERENCES outbreaks(outbreak_id) ON DELETE CASCADE,
    species VARCHAR(50),
    total_susceptible INTEGER,
    cases INTEGER,
    deaths INTEGER,
    observation_date DATE
);

-- Table for samples collected during an investigation
CREATE TABLE samples (
    sample_id SERIAL PRIMARY KEY,
    outbreak_id INTEGER REFERENCES outbreaks(outbreak_id) ON DELETE CASCADE,
    field_sample_id VARCHAR(100),
    animal_id VARCHAR(50),
    sample_type VARCHAR(100),
    laboratory VARCHAR(100),
    submission_date DATE,
    status VARCHAR(50) DEFAULT 'Collected' -- Collected, In Transit, Received, Testing, Results Available
);
-- ... (keep all the existing table definitions) ...

-- Table to store contact tracing links (the network edges)
CREATE TABLE contact_tracing_links (
    link_id SERIAL PRIMARY KEY,
    source_outbreak_id INTEGER REFERENCES outbreaks(outbreak_id) ON DELETE CASCADE,
    linked_location_name VARCHAR(255) NOT NULL,
    linked_location_type VARCHAR(50), -- e.g., Farm, Market, Water Point
    latitude DECIMAL(9, 6),
    longitude DECIMAL(9, 6),
    contact_date DATE,
    contact_type VARCHAR(100), -- e.g., Animal Movement, Vehicle, Personnel
    direction VARCHAR(20), -- Trace-back or Trace-forward
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
-- ... (keep all the existing table definitions) ...

-- Table to store outputs from Participatory Epidemiology sessions
CREATE TABLE pe_sessions (
    session_id SERIAL PRIMARY KEY,
    outbreak_id INTEGER REFERENCES outbreaks(outbreak_id) ON DELETE CASCADE, -- Optional link to a specific outbreak
    woreda_code VARCHAR(20) REFERENCES admin_woredas(woreda_code),
    session_date DATE NOT NULL,
    facilitator_name VARCHAR(255),
    pe_method VARCHAR(100) NOT NULL, -- e.g., Proportional Piling, Matrix Scoring
    session_data JSONB NOT NULL, -- Flexible field for all results
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ... (keep all other table definitions) ...

-- Table for samples collected during an investigation
CREATE TABLE samples (
    sample_id SERIAL PRIMARY KEY,
    outbreak_id INTEGER REFERENCES outbreaks(outbreak_id) ON DELETE CASCADE,
    field_sample_id VARCHAR(100) UNIQUE NOT NULL, -- Field ID must be unique
    animal_id VARCHAR(50),
    sample_type VARCHAR(100),
    laboratory VARCHAR(100),
    submission_date DATE,
    status VARCHAR(50) DEFAULT 'Collected', -- Collected, In Transit, Received, Testing, Results Available, Rejected
    result VARCHAR(100), -- e.g., Positive, Negative, Inconclusive
    result_details TEXT, -- e.g., 'FMD-Type A', 'Brucella abortus positive'
    result_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ... (keep all the existing table definitions) ...

-- Table for tracking inventory of veterinary supplies
CREATE TABLE inventory (
    item_id SERIAL PRIMARY KEY,
    item_name VARCHAR(255) NOT NULL, -- e.g., 'FMD Vaccine (Type O)', 'Syringes (10ml)'
    item_type VARCHAR(50) NOT NULL, -- e.g., Vaccine, PPE, Disinfectant, Kit
    quantity INTEGER NOT NULL,
    unit VARCHAR(50), -- e.g., doses, units, liters
    location VARCHAR(100) NOT NULL, -- e.g., 'National Store', 'Jinka Regional Store'
    expiry_date DATE,
    batch_number VARCHAR(100),
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- Table for veterinary personnel roster
CREATE TABLE personnel (
    personnel_id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    qualification VARCHAR(100), -- e.g., DVM, FETP Graduate, Animal Health Tech
    current_station VARCHAR(100), -- e.g., 'Bena Tsemay Woreda Office'
    specialization TEXT[], -- e.g., {'Epidemiology', 'Vaccinology'}
    contact_number VARCHAR(50),
    status VARCHAR(50) DEFAULT 'Available' -- Available, Deployed, On Leave
);
-- ... (keep all the existing table definitions) ...

-- Table for managing API access for external partners
CREATE TABLE api_keys (
    key_id SERIAL PRIMARY KEY,
    partner_name VARCHAR(255) UNIQUE NOT NULL, -- e.g., 'Ministry of Health - EPHI'
    api_key VARCHAR(255) UNIQUE NOT NULL,
    permissions TEXT[], -- e.g., {'read:zoonotic_outbreaks'}
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
-- ... (keep all the existing table definitions) ...

-- Table for known locations in the market chain (nodes)
CREATE TABLE locations (
    location_id SERIAL PRIMARY KEY,
    location_name VARCHAR(255) NOT NULL,
    location_type VARCHAR(50) NOT NULL, -- e.g., Market, Feedlot, Woreda, Slaughterhouse
    woreda_code VARCHAR(20) REFERENCES admin_woredas(woreda_code),
    latitude DECIMAL(9, 6),
    longitude DECIMAL(9, 6),
    UNIQUE (location_name, location_type)
);

-- Table to log livestock movement events (edges)
CREATE TABLE movements (
    movement_id SERIAL PRIMARY KEY,
    origin_location_id INTEGER REFERENCES locations(location_id),
    destination_location_id INTEGER REFERENCES locations(location_id),
    movement_date DATE NOT NULL,
    species VARCHAR(50),
    num_animals INTEGER,
    data_source VARCHAR(100) -- e.g., 'ET-LITS', 'Field Report'
);

-- ... (keep all the existing table definitions) ...

-- Table for storing molecular data linked to a sample
CREATE TABLE molecular_data (
    molecular_id SERIAL PRIMARY KEY,
    sample_id INTEGER UNIQUE REFERENCES samples(sample_id) ON DELETE CASCADE,
    serotype VARCHAR(50),
    genotype VARCHAR(50),
    sequence_data TEXT, -- For storing FASTA sequences
    phylogenetic_tree_newick TEXT, -- For storing tree data in Newick format
    analysis_date DATE
);

-- ... (keep all the existing table definitions) ...

-- Table for logging communication and engagement activities
CREATE TABLE communications_log (
    log_id SERIAL PRIMARY KEY,
    outbreak_id INTEGER REFERENCES outbreaks(outbreak_id) ON DELETE CASCADE,
    activity_type VARCHAR(100) NOT NULL, -- e.g., 'SMS Alert', 'Village Meeting', 'Poster Distribution'
    target_audience VARCHAR(255), -- e.g., 'Farmers in Bena Tsemay', 'General Public'
    message_content TEXT,
    communication_date DATE NOT NULL,
    officer_name VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

\echo 'Database schema v10 created successfully.'
