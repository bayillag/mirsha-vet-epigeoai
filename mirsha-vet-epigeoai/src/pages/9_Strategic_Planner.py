import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
from src.core import database as db

st.set_page_config(page_title="Strategic Planner", page_icon="🧭", layout="wide")

st.title("🧭 Strategic Surveillance Planner (Module 8)")
st.markdown("Design, monitor, and evaluate national surveillance programs using historical data and performance metrics.")

# --- Main Page Layout with Tabs ---
tab1, tab2 = st.tabs(["Surveillance Performance Dashboard", "Risk-Based Survey Planning Tool"])

# --- Tab 1: Performance Dashboard ---
with tab1:
    st.header("Surveillance System Performance Dashboard")
    st.info("This dashboard provides Key Performance Indicators (KPIs) to evaluate the effectiveness of the national reporting network.")

    # Load performance data
    performance_df, national_avg_response = db.get_surveillance_performance_data()

    if performance_df.empty:
        st.warning("No performance data available yet. Complete some investigation reports to generate metrics.")
    else:
        # --- Display KPIs ---
        st.subheader("National KPIs")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Woredas Reporting", f"{performance_df['woreda_name'].nunique()}")
        col2.metric("Total Reports Filed", f"{performance_df['total_reports'].sum()}")
        col3.metric("Average Response Time (Days)", f"{national_avg_response:.1f}")

        # --- Display Charts and Tables ---
        st.subheader("Performance by Region")
        
        # Bar chart for total reports by region
        reports_by_region = performance_df.groupby('region_name')['total_reports'].sum().sort_values(ascending=False)
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        reports_by_region.plot(kind='bar', ax=ax1, color='skyblue')
        ax1.set_title("Total Outbreak Reports per Region")
        ax1.set_ylabel("Number of Reports")
        ax1.set_xlabel("Region")
        plt.xticks(rotation=45, ha='right')
        st.pyplot(fig1)

        st.subheader("Detailed Woreda Performance Data")
        st.dataframe(performance_df, use_container_width=True)


# --- Tab 2: Risk-Based Survey Planning Tool ---
with tab2:
    st.header("Risk-Based Survey Planning Tool")
    st.info("Use historical outbreak data to identify high-risk areas for targeted surveillance activities (e.g., serosurveys, active case finding).")

    # --- User Input ---
    disease_list = ["FMD", "PPR", "Anthrax", "LSD", "CBPP"] # Should be fetched from DB
    selected_disease = st.selectbox("Select a Disease to Plan For", options=disease_list)

    if selected_disease:
        # Fetch historical data for the chosen disease
        hotspot_gdf = db.get_historical_hotspots(selected_disease)

        if hotspot_gdf.empty:
            st.warning(f"No historical data available for {selected_disease}.")
        else:
            st.subheader(f"Historical Distribution of {selected_disease} Cases")
            
            # Create a choropleth map of historical cases
            map_center = [hotspot_gdf.unary_union.centroid.y, hotspot_gdf.unary_union.centroid.x]
            m = folium.Map(location=map_center, zoom_start=6, tiles="CartoDB positron")

            folium.Choropleth(
                geo_data=hotspot_gdf.to_json(),
                data=hotspot_gdf,
                columns=['woreda_code', 'total_cases'],
                key_on='feature.properties.woreda_code',
                fill_color='Reds',
                fill_opacity=0.8,
                line_opacity=0.2,
                legend_name=f'Total Historical Cases of {selected_disease}',
            ).add_to(m)

            st_folium(m, use_container_width=True, height=500)
            
            # --- Interactive Planning ---
            st.subheader("Define High-Risk Stratum")
            
            # Use a slider to define the risk threshold
            max_cases = int(hotspot_gdf['total_cases'].max())
            if max_cases > 0:
                threshold = st.slider(
                    "Select minimum number of historical cases to define a woreda as 'High-Risk'",
                    min_value=1,
                    max_value=max_cases,
                    value=max(1, int(max_cases * 0.5)) # Default to 50% of max
                )
                
                # Filter to get the high-risk woredas
                high_risk_woredas = hotspot_gdf[hotspot_gdf['total_cases'] >= threshold]
                
                st.metric("Number of Woredas in High-Risk Stratum", len(high_risk_woredas))
                
                st.markdown("**Sampling Frame for Risk-Based Survey:**")
                st.dataframe(
                    high_risk_woredas[['woreda_name', 'total_cases']].sort_values(by='total_cases', ascending=False),
                    use_container_width=True
                )
                
                @st.cache_data
                def convert_df_to_csv(df):
                    return df.to_csv(index=False).encode('utf-8')

                csv = convert_df_to_csv(high_risk_woredas[['woreda_name', 'woreda_code', 'total_cases']])
                
                st.download_button(
                    label="Download Sampling Frame as CSV",
                    data=csv,
                    file_name=f'risk_based_survey_frame_{selected_disease}.csv',
                    mime='text/csv',
                )
            else:
                st.info("No cases in the dataset to set a threshold.")
