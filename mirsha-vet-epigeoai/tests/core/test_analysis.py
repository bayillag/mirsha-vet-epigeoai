import geopandas as gpd
from shapely.geometry import Polygon
from src.core import analysis as an

def test_calculate_lisa_hotspot():
    """
    Tests the LISA calculation on a simple GeoDataFrame with a clear hotspot.
    """
    # Create a 2x2 grid of polygons
    p1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]) # Bottom-left
    p2 = Polygon([(1, 0), (2, 0), (2, 1), (1, 1)]) # Bottom-right (hotspot)
    p3 = Polygon([(0, 1), (1, 1), (1, 2), (0, 2)]) # Top-left
    p4 = Polygon([(1, 1), (2, 1), (2, 2), (1, 2)]) # Top-right (hotspot)

    gdf = gpd.GeoDataFrame([
        {'id': 1, 'total_cases': 5},
        {'id': 2, 'total_cases': 100},
        {'id': 3, 'total_cases': 10},
        {'id': 4, 'total_cases': 120}
    ], geometry=[p1, p2, p3, p4], crs="EPSG:4326")

    # Run the LISA analysis
    result_gdf = an.calculate_lisa(gdf, 'total_cases')

    # Assertions
    assert 'cluster_type' in result_gdf.columns
    # Check that the high-value polygon surrounded by another high-value polygon is a hotspot
    hotspot_cluster_type = result_gdf[result_gdf['id'] == 4]['cluster_type'].iloc[0]
    assert hotspot_cluster_type == 'High-High (Hotspot)'