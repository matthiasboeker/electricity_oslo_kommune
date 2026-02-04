import json 
from pathlib import Path
from api_connections.weather_api_connection import WeatherAPIConnection
import os
from dotenv import load_dotenv

load_dotenv()

def read_json(file_path: Path) -> dict:
    with open(file_path, 'r') as f:
        return json.load(f)
    

def allocate_closest_weather_station(address_geo_locations: dict, weather_stations: dict) -> dict:
    allocated_stations = {}
    for address, coords in address_geo_locations.items():
        min_distance = float('inf')
        closest_station_id = None
        for station in weather_stations.get('data', []):
            if 'geometry' not in station:
                continue
            station_id = station['id']
            station_lat = station['geometry']['coordinates'][1]
            station_lon = station['geometry']['coordinates'][0]
            if coords['latitude'] is None or coords['longitude'] is None:
                continue
            distance = ((float(coords['latitude']) - station_lat) ** 2 + (float(coords['longitude']) - station_lon) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                closest_station_id = station_id
        allocated_stations[address] = {"station_id": closest_station_id, "station_location": (station_lat, station_lon), "address_location": (coords['latitude'], coords['longitude'])}
    return allocated_stations

def main():
    address_geo_locations = read_json(Path('data/address_geo_locations.json'))
    weather_connector = WeatherAPIConnection(
        client_id=os.getenv("FROST_CLIENT_ID"),
        client_secret=os.getenv("FROST_CLIENT_SECRET")  
    )
    weather_stations = weather_connector.get_sources({'name': 'OSLO*'})
    allocated_stations = allocate_closest_weather_station(address_geo_locations, weather_stations)
    with open(Path('data/address_closest_weather_stations.json'), 'w') as f:
        json.dump(allocated_stations, f, indent=4)

if __name__ == "__main__":
    main()