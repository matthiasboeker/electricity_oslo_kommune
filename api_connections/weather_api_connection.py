from typing import List
import requests
import pandas as pd


class WeatherAPIConnection:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id =  client_id 
        self.client_secret = client_secret
        self.base_url = "https://frost.met.no"

    def get_sources(self, kwargs) -> dict:
        endpoint = f"{self.base_url}/sources/v0.jsonld"
        headers = {
            'Accept': 'application/json',
        }
        params = kwargs
        response = requests.get(endpoint, headers=headers, params=params, auth=(self.client_id, self.client_secret))
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def get_weather_data(self, sources: List[str], elements: List[str], start_time: str, end_time: str) -> dict:
        endpoint = f"{self.base_url}/observations/v0.jsonld"
        headers = {
            'Accept': 'application/json',
        }
        parameters = {
            'sources': ','.join(sources),      
            'elements': ','.join(elements),
            'referencetime': f"{start_time}/{end_time}",
        }
        response = requests.get(endpoint, headers=headers, params=parameters, auth=(self.client_id, self.client_secret))
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            response.raise_for_status()