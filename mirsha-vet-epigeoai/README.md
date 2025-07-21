# Mirsha VetEpiGeoAI: Comprehensive Platform

[![License: MIT](https://img-shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bayillag/mirsha-vet-epigeoai/blob/main/notebooks/Mirsha_VetEpiGeoAI_Analysis.ipynb)
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/bayillag/mirsha-vet-epigeoai)

**Mirsha VetEpiGeoAI** is an integrated, workflow-centric national platform designed to support the entire lifecycle of animal health management in Ethiopia—from field-level outbreak investigation to strategic national surveillance, predictive modeling, and policy support.

This platform is architected into four primary divisions, each containing specialized modules to serve users from field veterinarians to national policymakers.

---

## The Four Divisions of Mirsha VetEpiGeoAI

### Division I: Field Operations & Outbreak Response
*Core tools for frontline personnel to manage active outbreaks.*
*   **Module 1:** Outbreak Reporting & Triage
*   **Module 2:** Field Investigation Hub (Digital Field Kit)
*   **Module 3:** Contact Tracing Module
*   **Module 5:** Biosecurity & Disinfection Protocols Hub

### Division II: Analytics & Laboratory Integration
*The analytical engine that transforms raw field data into structured intelligence.*
*   **Module 4:** Analytics & Surveillance Dashboard
*   **Module 7:** Laboratory Information Management System (LIMS) Gateway
*   **Module 13:** Livestock Movement & Market Chain Analysis
*   **Module 14:** Molecular & Genomic Surveillance Dashboard

### Division III: Strategic Planning & Policy Support
*High-level tools for program design, economic justification, and long-term strategy.*
*   **Module 8:** Strategic Surveillance Planner
*   **Module 9:** Predictive Modeling & Early Warning System (EWS)
*   **Module 10:** Resource Management & Logistics Hub
*   **Module 11:** Economic Impact & Cost-Benefit Analysis Tool

### Division IV: Communication & Capacity Building
*Focuses on the human dimensions of animal health: stakeholder engagement and workforce development.*
*   **Module 6:** Participatory Epidemiology (PE) Toolkit
*   **Module 12:** "One Health" Data Gateway
*   **Module 15:** Public Communication & Stakeholder Engagement Portal
*   **Module 16:** Training, Simulation & Capacity Building Platform

---

## Getting Started

This repository is fully configured for **GitHub Codespaces**, which provides a complete, cloud-based development environment.

1.  **Launch Codespace:** Click the "Open in GitHub Codespaces" badge above.
2.  **Wait for Setup:** The environment will automatically build and start the application and database containers, install all dependencies, and configure VS Code. This may take several minutes on the first run.
3.  **Initialize the Database:** Open a terminal in the Codespace (`Ctrl+\`` or `Cmd+\``) and run the setup script:
    ```bash
    # First, load the spatial data (shapefiles)
    docker exec -i mirsha_db shp2pgsql -s 4326 -I /workspaces/mirsha-vet-epigeoai/data/raw/gis/your_shapefile.shp public.admin_woredas | docker exec -i mirsha_db psql -d vet_epigeoai_db -U vet_user

    # Then, create the schema and load tabular data
    python src/scripts/setup_database.py
    ```
4.  **Run the Dashboard:**
    ```bash
    streamlit run app.py
    ```
    A pop-up will allow you to open the running dashboard in your browser.
