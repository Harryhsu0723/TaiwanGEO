import geopandas as gpd
import os
import sys

def convert_shp_to_geojson(input_path):
    """
    Converts a Shapefile to GeoJSON, transforming CRS to WGS84 (EPSG:4326).
    """
    try:
        # Read the shapefile
        print(f"Reading {input_path}...")
        gdf = gpd.read_file(input_path)
        
        # Check CRS and transform if necessary
        # If CRS is missing, we assume TWD97 (EPSG:3826) based on file naming context,
        # but it's safer to let the user know or default to it if not set.
        if gdf.crs is None:
            print("Warning: CRS not found in shapefile. Assuming TWD97 (EPSG:3826).")
            gdf.set_crs(epsg=3826, inplace=True)
        
        print(f"Original CRS: {gdf.crs}")
        
        if gdf.crs.to_string() != "EPSG:4326":
            print("Reprojecting to WGS84 (EPSG:4326)...")
            gdf = gdf.to_crs(epsg=4326)
            
        # Define output path
        output_path = os.path.splitext(input_path)[0] + ".geojson"
        
        # Save to GeoJSON
        print(f"Saving to {output_path}...")
        gdf.to_file(output_path, driver="GeoJSON")
        print("Conversion successful!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python shp_to_geojson.py <path_to_shapefile>")
    else:
        convert_shp_to_geojson(sys.argv[1])
