import json
import geopandas as gpd
import topojson as tp
from pathlib import Path
from shapely.geometry import Point
import pandas as pd

def read_csv_data(file_path: Path) -> pd.DataFrame:
    """Read electricity consumption data from a CSV file."""
    return pd.read_csv(file_path, engine='python')

def load_in_bydeler_geopandas(path_to_data: Path) -> gpd.GeoDataFrame:
    with open(path_to_data, 'r', encoding='utf-8') as f:
        topo_data = json.load(f)

    topology = tp.Topology(topo_data, object_name='Bydeler')
    gdf = topology.to_gdf()
    gdf = gdf.set_crs('EPSG:4326', allow_override=True)
    return gdf

def find_bydel(lat: float, lon: float, gdf: gpd.GeoDataFrame):
    point = Point(lon, lat)
    for idx, row in gdf.iterrows():
        if row.geometry.contains(point):
            return {
                'BYDELSNAVN': row['BYDELSNAVN'],
                'BYDEL': row['BYDEL'],
                'Kombinert': row['Kombinert']
            }
    return {
                'BYDELSNAVN': None,
                'BYDEL': None,
                'Kombinert': None
            }

def allocate_bydel_to_data(df, gdf: gpd.GeoDataFrame):
    bydel_info = []
    for _, row in df.iterrows():
        lat = row['latitude']
        lon = row['longitude']
        if pd.notnull(lat) and pd.notnull(lon):
            bydel = find_bydel(lat, lon, gdf)
            bydel_info.append(bydel)
        else:
            bydel_info.append({
                'BYDELSNAVN': None,
                'BYDEL': None,
                'Kombinert': None
            })
    bydel_df = pd.DataFrame(bydel_info)
    df = pd.concat([df.reset_index(drop=True), bydel_df.reset_index(drop=True)], axis=1)
    return df


def main():
    path_to_electricity_file = Path(__file__).parent / 'data' / 'stromforbruk_with_geo.csv'
    path_to_bydel_topojson = Path(__file__).parent / 'data' / 'Bydeler_Oslo_m_marka.json'
    electricity_df = read_csv_data(path_to_electricity_file)
    print(electricity_df.head())
    bydel_gdf = load_in_bydeler_geopandas(path_to_bydel_topojson)
    df = allocate_bydel_to_data(electricity_df, bydel_gdf)
    df.to_csv(Path(__file__).parent / 'data' / 'stromforbruk_with_bydel.csv', index=False)

if __name__ == "__main__":
    main()