-- Creates the database schema for Mirsha VetEpiGeoAI
-- Compliant with the Ethiopian National Livestock Data Standard

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Drop existing tables for a clean setup
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
    disease_code VARCHAR(20) REFERENCES diseases(disease_code),
    woreda_code VARCHAR(20) REFERENCES admin_woredas(woreda_code),
    report_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'Suspected', -- Suspected, Confirmed, Resolved
    investigator_name VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table for line-listing of cases within an outbreak
CREATE TABLE outbreak_cases (
    case_id SERIAL PRIMARY KEY,
    outbreak_id INTEGER REFERENCES outbreaks(outbreak_id),
    species VARCHAR(50),
    total_susceptible INTEGER,
    cases INTEGER,
    deaths INTEGER,
    observation_date DATE
);

\echo 'Database schema created successfully.'
