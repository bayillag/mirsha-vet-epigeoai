import streamlit as st
import pandas as pd
import folium
import uuid
from streamlit_folium import st_folium
from src.core import database as db # We still need some functions from our core DB module

st.set_page_config(page_title="One Health Gateway", page_icon="🤝", layout="wide")

st.title('🤝 "One Health" Data Gateway (Module 12)')
st.markdown("Manage secure data sharing with human health partners and visualize joint outbreak data.")

# --- Tabbed Interface ---
tab1, tab2 = st.tabs(["API Key Management", "Joint Outbreak Map"])

# --- Tab 1: API Key Management ---
with tab1:
    st.header("API Key Management for External Partners")
    st.info("Create and manage API keys to provide secure, read-only access to zoonotic outbreak data.")
    
    # In a real app, this section should be restricted to administrators
    
    with st.form("api_key_form"):
        st.subheader("Generate New API Key")
        partner_name = st.text_input("Partner Name (e.g., 'Ministry of Health - EPHI') *")
        permissions = st.multiselect(
            "Permissions",
            options=["read:zoonotic_outbreaks"],
            default=["read:zoonotic_outbreaks"]
        )
        
        generate_button = st.form_submit_button("Generate Key")

    if generate_button and partner_name:
        new_key = f"mvga-{uuid.uuid4()}" # Generate a new unique key
        
        # --- Database interaction to save the key ---
        # This is a simplified version. A real app would hash the key before storing.
        conn = db.get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO api_keys (partner_name, api_key, permissions) VALUES (%s, %s, %s)",
                        (partner_name, new_key, permissions)
                    )
                    conn.commit()
                st.success(f"API Key generated successfully for {partner_name}!")
                st.code(new_key, language=None)
                st.warning("Please copy this key and share it with the partner. It will not be shown again.")
            except Exception as e:
                st.error(f"Failed to save key to database. Partner name might already exist. Error: {e}")
        else:
            st.error("Database connection failed.")

    st.subheader("Active API Keys")
    # Fetch and display existing keys
    conn = db.get_db_connection()
    if conn:
        active_keys_df = pd.read_sql("SELECT key_id, partner_name, permissions, is_active, created_at FROM api_keys", conn)
        st.dataframe(active_keys_df, use_container_width=True)


# --- Tab 2: Joint Outbreak Map ---
with tab2:
    st.header("Joint Animal-Human Outbreak Map")
    st.info("This map visualizes confirmed zoonotic animal outbreaks alongside manually uploaded human case data for correlation analysis.")
    
    # --- Data Loading ---
    # In a real scenario, the animal data would come from our API endpoint.
    # We will simulate this by fetching directly from the DB for this dashboard.
    @st.cache_data
    def get_zoonotic_animal_data():
        conn = db.get_db_connection()
        ZOONOTIC_DISEASES = ['Anthrax', 'Rabies', 'Rift Valley Fever']
        sql = """
            SELECT o.outbreak_id, d.disease_name, a.woreda_name, a.geom
            FROM outbreaks o
            JOIN diseases d ON o.disease_code = d.disease_code
            JOIN admin_woredas a ON o.woreda_code = a.woreda_code
            WHERE o.status = 'Confirmed' AND d.disease_name = ANY(%s);
        """
        return gpd.read_postgis(sql, conn, geom_col='geom', params=(ZOONOTIC_DISEASES,))

    animal_gdf = get_zoonotic_animal_data()
    
    # --- Human Case Data Upload ---
    st.subheader("Upload Human Case Data")
    uploaded_file = st.file_uploader(
        "Upload a CSV with human case locations (columns: 'latitude', 'longitude', 'disease')",
        type="csv"
    )
    
    map_center = [9.14, 40.48] # Ethiopia center
    m_joint = folium.Map(location=map_center, zoom_start=6, tiles="CartoDB positron")

    # Add animal outbreaks to map
    if not animal_gdf.empty:
        folium.GeoJson(
            animal_gdf,
            style_function=lambda x: {'fillColor': 'orange', 'color': 'orange', 'weight': 2, 'fillOpacity': 0.4},
            tooltip=folium.GeoJsonTooltip(fields=['woreda_name', 'disease_name']),
            name="Animal Outbreak Zones (Woredas)"
        ).add_to(m_joint)

    # Add human cases to map if file is uploaded
    if uploaded_file is not None:
        human_df = pd.read_csv(uploaded_file)
        st.write("Human cases loaded:", human_df.shape[0])
        
        for _, row in human_df.iterrows():
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=5,
                color='red',
                fill=True,
                fill_color='red',
                fill_opacity=0.8,
                popup=f"Human Case: {row.get('disease', 'Unknown')}",
                name="Human Cases"
            ).add_to(m_joint)

    folium.LayerControl().add_to(m_joint)
    st_folium(m_joint, use_container_width=True, height=600)