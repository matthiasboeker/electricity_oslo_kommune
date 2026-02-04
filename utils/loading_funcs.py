from pathlib import Path
import pandas as pd
import json
import geopandas as gpd
import topojson as tp

def read_csv_data(file_path: Path, sep: str = ',') -> pd.DataFrame:
    """Load CSV data into DataFrame."""
    return pd.read_csv(file_path, engine='python', sep=sep)



def load_bydeler_geodata(path_to_data: Path) -> gpd.GeoDataFrame:
    """Load bydeler topology data as GeoDataFrame."""
    with open(path_to_data, 'r', encoding='utf-8') as f:
        topo_data = json.load(f)
    
    topology = tp.Topology(topo_data, object_name='Bydeler')
    gdf = topology.to_gdf()
    gdf = gdf.set_crs('EPSG:4326', allow_override=True)
    return gdf

def load_data(file_path):
    return pd.read_csv(file_path, engine='python')   