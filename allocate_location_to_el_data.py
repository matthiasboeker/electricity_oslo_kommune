from pathlib import Path
from OSMPythonTools.nominatim import Nominatim
import pandas as pd
import json


def read_csv_data(file_path: str) -> pd.DataFrame:
    """Read electricity consumption data from a CSV file."""
    return pd.read_csv(file_path, engine='python', sep=';', decimal='.')

def read_json(file_path: Path) -> pd.DataFrame:
    with open(file_path, 'r') as f:
        return json.load(f)

def get_location_info_per_address(df: pd.DataFrame) -> dict:
    """Allocate geographical locations to electricity consumption data."""
    nominatim = Nominatim()
    location_geo_info = {}
    
    for address in df['addresse'].unique():
        location = nominatim.query(f"{address}, Oslo, Norway")
        if location.toJSON():
            location_geo_info[address] = {
                'latitude': float(location.toJSON()[0]['lat']),
                'longitude': float(location.toJSON()[0]['lon'])
            }
        else:
            location_geo_info[address] = {
                'latitude': None,
                'longitude': None
            }
    return location_geo_info

def allocate_location_to_el_data(df: pd.DataFrame, geo_locations: dict) -> pd.DataFrame:
    """Add geographical location data to the electricity consumption DataFrame."""
    df['latitude'] = df['addresse'].apply(lambda addr: geo_locations.get(addr, {}).get('latitude'))
    df['longitude'] = df['addresse'].apply(lambda addr: geo_locations.get(addr, {}).get('longitude'))
    return df


def main():
    data_file = Path('data/stromforbruk.csv')
    df = read_csv_data(data_file)
    geo_locations_per_address = get_location_info_per_address(df)
    geo_locations_per_address = read_json(Path('data/address_geo_locations.json'))
    electricity_location_data = allocate_location_to_el_data(df, geo_locations_per_address)
    electricity_location_data.to_csv(Path('data/stromforbruk_with_geo.csv'), index=False)

if __name__ == "__main__":
    main()