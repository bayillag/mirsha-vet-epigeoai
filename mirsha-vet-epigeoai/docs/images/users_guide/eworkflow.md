---

### **Mirsha VetEpiGeoAI: End-to-End User Workflow**

This workflow is divided into three main phases: **Setup**, **Outbreak Response**, and **Strategic Analysis & Planning**.

#### **Phase 1: Initial Platform Setup (One-Time Setup)**

This phase is performed once to initialize the entire environment and populate it with data.

**Step 1: Launch the Environment**
*   **Action:** Go to the GitHub repository (`github.com/bayillag/mirsha-vet-epigeoai`). Click the "<> Code" button, go to the "Codespaces" tab, and click **"Create codespace on main"**.
*   **Result:** GitHub builds the environment. After a few minutes, a complete VS Code instance opens in your browser, with the database service already running in the background.

**Step 2: Generate All Necessary Data**
*   **Action:** Open a terminal in the Codespace (`Ctrl+` or `Cmd+`).
*   Run the three data generation scripts in order:
    1.  **Create GIS Data:**
        ```bash
        python src/scripts/generate_gis_data.py
        ```
    2.  **Create Mock Case Data:**
        ```bash
        python src/scripts/generate_mock_cases.py
        ```
    3.  **Create External Risk Factor Data:**
        ```bash
        python src/scripts/generate_risk_data.py
        ```
*   **Result:** Your `data/raw/` and `data/external/` folders are now populated with all the necessary source files.

**Step 3: Initialize and Populate the Database**
*   **Action:** In the same terminal, run the master database setup script.
    ```bash
    python src/scripts/setup_database.py
    ```
*   **Result:** The script creates all database tables and populates them with the woreda geometries and mock outbreak data. The platform's backend is now live and ready.

**Step 4: Launch the Main Application**
*   **Action:** In the terminal, start the Streamlit dashboard.
    ```bash
    streamlit run app.py
    ```
*   **Result:** A notification will appear in VS Code. Click **"Open in Browser"**. The Mirsha VetEpiGeoAI homepage will open in a new tab.

---

#### **Phase 2: Simulating an Outbreak Response (Field & Manager Workflow)**

Imagine you are both a field officer and a regional manager responding to a new event.

**Step 5: File an Initial Report (Module 1)**
*   **Action:** In the Streamlit app's sidebar, navigate to the **`1_New_Outbreak_Report`** page.
*   **Simulate:** Fill out the form for a suspected FMD case in "Hamer" woreda. Click **"Submit Report"**.
*   **Result:** The report is saved to the database with a status of "Unassigned."

**Step 6: Triage and Assign the Report (Module 1)**
*   **Action:** Navigate to the **`2_Triage_Dashboard`** page.
*   **Simulate:** You will see the new report from "Hamer" in the list. Select an investigator (e.g., "Dr. Alemayehu") from the dropdown and click **"Assign"**.
*   **Result:** The report is updated in the database. It disappears from the Triage Dashboard and is now assigned.

**Step 7: Conduct the Field Investigation (Module 2, 5, 6)**
*   **Action:** Navigate to the **`3_Field_Investigation_Hub`** page.
*   **Simulate (as Dr. Alemayehu):**
    1.  Select the newly assigned outbreak ID for Hamer from the dropdown.
    2.  **Use the Biosecurity Hub (Module 5):** Before "entering the farm," open the **`5_Biosecurity_Hub`** page. Select "Foot-and-mouth disease" to review the required PPE and disinfection protocols.
    3.  **Use the PE Toolkit (Module 6):** Open the **`6_PE_Toolkit`** page. Simulate a "Proportional Piling" exercise with the community to understand their main concerns and save the results.
    4.  **File the Report:** Go back to the **Field Investigation Hub**. Fill out the full investigation form: confirm the date, create a line list of cases (e.g., 200 susceptible cattle, 30 cases, 5 deaths), check the relevant clinical signs, and log two blood samples you "collected."
    5.  Click **"Submit Final Investigation Report"**.
*   **Result:** The outbreak record is updated with detailed clinical data, case numbers, and sample records. The status changes to "Completed."

**Step 8: Submit Lab Results (Module 7)**
*   **Action:** Navigate to the **`8_Lab_Results_Entry`** page.
*   **Simulate (as a lab technician):**
    1.  Enter the password (`veteplab123`).
    2.  Enter one of the Field Sample IDs you created in the previous step.
    3.  Fill out the form: Result = "Positive," Result Details = "FMD-Type O," and select today's date. Click **"Submit Final Result"**.
*   **Result:** The sample is updated in the database. Crucially, the parent outbreak's status is automatically updated from "Completed" to **"Confirmed"**.

**Step 9: Trace Contacts (Module 3)**
*   **Action:** Navigate to the **`4_Contact_Tracing`** page.
*   **Simulate:** Select the now-confirmed FMD outbreak in Hamer. The tracing window is automatically calculated. Add two links:
    1.  A **Trace-back** link to a market where the animals were purchased.
    2.  A **Trace-forward** link to a neighboring woreda where animals were recently moved.
*   **Result:** An interactive network map is built, showing the potential source and spread of the outbreak.

---

#### **Phase 3: Strategic Analysis & National Planning**

Imagine you are now a national-level epidemiologist or ministry official.

**Step 10: Analyze the Situation (Module 4)**
*   **Action:** Navigate to the **`1_Analytics_Dashboard`**.
*   **Simulate:**
    1.  Use the filters to view all "FMD" cases.
    2.  On the **Choropleth Map** tab, visualize the Attack Rate per woreda.
    3.  On the **Hotspot Analysis** tab, run the LISA analysis to see if the Hamer outbreak is part of a statistically significant cluster.

**Step 11: Analyze the Market Chain (Module 13)**
*   **Action:** Go to the **`14_Market_Chain_Analysis`** page.
*   **Simulate:** Filter for "Cattle" movements in the last 90 days.
*   **Result:** An interactive network graph shows the busiest markets and trade routes, helping you understand how the disease might have spread from the market you identified in Step 9.

**Step 12: View Molecular Data (Module 14)**
*   **Action:** Go to the **`15_Molecular_Surveillance`** page.
*   **Simulate:** Filter for "FMD." The dashboard will show the geographic distribution of different serotypes (e.g., Type O and Type A) based on historical lab data.

**Step 13: Plan a Strategic Survey (Module 8)**
*   **Action:** Go to the **`9_Strategic_Planner`** page.
*   **Simulate:**
    1.  Review the **Performance Dashboard** tab to check the reporting timeliness for the South Omo region.
    2.  Switch to the **Risk-Based Survey Planning Tool** tab. Select "FMD." The map shows historical hotspots.
    3.  Use the slider to define a high-risk stratum and generate a downloadable CSV of woredas for a targeted FMD serosurvey.

**Step 14: Justify the Budget (Module 11)**
*   **Action:** Go to the **`12_Economic_Impact_Hub`** page.
*   **Simulate:**
    1.  On the **Outbreak Cost Calculator**, select the Hamer FMD outbreak ID to see the estimated direct economic loss.
    2.  On the **Cost-Benefit Planner**, model a national FMD vaccination campaign, entering its estimated cost and effectiveness to calculate the potential Return on Investment (ROI).

**Step 15: Communicate with Stakeholders (Module 15 & 12)**
*   **Action:** Go to the **`16_Communications_Hub`** page.
*   **Simulate:**
    1.  Use the **Campaign Builder** to generate a standardized SMS alert for all farmers in the Hamer control zone.
    2.  View the **Public Outbreak Map** to see how the quarantine zone is displayed to the public (without revealing specific farm locations).
    3.  Go to the **`13_One_Health_Gateway`** and use the **Joint Map** to visualize your animal outbreak data alongside a sample CSV of human cases you can upload.

**Step 16: Train New Staff (Module 16)**
*   **Action:** Go to the **`17_Training_Simulation`** page.
*   **Simulate:** Start the "Hypothetical FMD Outbreak (2021)" scenario. Step through the simulation day-by-day, making decisions and observing how your score and the instructor feedback change based on your actions.