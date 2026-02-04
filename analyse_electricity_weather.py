import json
from pathlib import Path
from api_connections.weather_api_connection import WeatherAPIConnection
import os
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt

from exploratory_analysis import clean_data_from_outliers, remove_negative_values

load_dotenv()

def plot_monthly_average_consumption_vs_weather(monthly_avg: pd.DataFrame, type_of_weather: str):
       # Create scatter plot
    fig, ax = plt.subplots(figsize=(12, 8))

    # Scatter med farge per måned
    scatter = ax.scatter(monthly_avg['forbruk_kwh'], 
                        monthly_avg[type_of_weather],
                        c=monthly_avg['month'],
                        cmap='twilight',  # God colormap for måneder
                        s=100,
                        alpha=0.7,
                        edgecolors='black',
                        linewidth=0.5)

    # Colorbar
    cbar = plt.colorbar(scatter, ax=ax, ticks=range(1, 13))
    cbar.set_label('Måned', fontsize=12, fontweight='bold')
    cbar.ax.set_yticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])

    # Labels
    ax.set_xlabel('Gjennomsnittlig Belysningsforbruk (kWh)', fontsize=12, fontweight='bold')
    if type_of_weather == 'mean_air_temp':
        ax.set_ylabel(f'Gjennomsnittlig Temperatur (°C)', fontsize=12, fontweight='bold')
    if type_of_weather == 'cloud_area_fraction':
        ax.set_ylabel(f'Skydekke', fontsize=12, fontweight='bold')
    ax.set_title(f'Belysningsforbruk vs. {type_of_weather} per Måned\n(2014-2022)', 
                fontsize=14, fontweight='bold')

    # Grid
    ax.grid(True, alpha=0.3, linestyle='--')

    # Add correlation
    correlation = monthly_avg['forbruk_kwh'].corr(monthly_avg[type_of_weather])
    ax.text(0.05, 0.95, f'Korrelasjon: {correlation:.3f}', 
            transform=ax.transAxes,
            fontsize=11,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    plt.savefig(f'belysning_vs_{type_of_weather}_scatter.png', dpi=300, bbox_inches='tight')
    plt.show()

    print(f"\n✓ Korrelasjon: {correlation:.3f}")


def transform_date_to_period(dataframe: pd.DataFrame):
    dato_dt = pd.to_datetime(dataframe['dato'])
    dataframe['year_month'] = dato_dt.dt.to_period('M')
    dataframe['month'] = dato_dt.dt.month
    return dataframe

def read_json(file_path: Path) -> dict:
    with open(file_path, 'r') as f:
        return json.load(f) 

def weather_data_to_dataframe(response: dict) -> pd.DataFrame:
    rows = []

    for item in response["data"]:
        date = pd.to_datetime(item["referenceTime"])
        # Fjern timezone før konvertering til Period
        date = date.tz_localize(None) if date.tz else date
        month_period = date.to_period("M")
        month_num = date.month


        # Hent verdier EN gang per item (ikke inne i loop)
        mean_air_temp = next((o['value'] for o in item["observations"] 
                             if (o["elementId"] == "mean(air_temperature P1M)") 
                             and (o.get("timeOffset") == "PT6H")), None)
        
        min_air_temp = next((o['value'] for o in item["observations"] 
                            if o["elementId"] == "min(air_temperature P1M)"), None)
        
        max_air_temp = next((o['value'] for o in item["observations"] 
                            if o["elementId"] == "max(air_temperature P1M)"), None)
        
        cloud_area_fraction = next((o['value'] for o in item["observations"] 
                                   if o["elementId"] == "mean(cloud_area_fraction P1M)"), None)

        # Legg til EN rad per måned
        rows.append({
            "year_month": month_period,
            "month": month_num,
            "mean_air_temp": mean_air_temp,
            "min_air_temp": min_air_temp,
            "max_air_temp": max_air_temp,
            "cloud_area_fraction": cloud_area_fraction,
        })

    return pd.DataFrame(rows)


def main():
    weater_connector = WeatherAPIConnection(
        client_id=os.getenv("FROST_CLIENT_ID"),  # Replace with your actual client ID
        client_secret=os.getenv("FROST_CLIENT_SECRET")  # Replace with your actual client secret
    )
    strom_forbruk = pd.read_csv('data/stromforbruk_with_geo.csv', engine='python')
    strom_forbruk = remove_negative_values(strom_forbruk)
    strom_forbruk = clean_data_from_outliers(strom_forbruk)
    strom_forbruk = transform_date_to_period(strom_forbruk)
    belysning_df = strom_forbruk[strom_forbruk['kategori'] == 'Belysning'].copy()


    weater_data = weater_connector.get_weather_data(
            sources=['SN18700'],
            elements=[
                'mean(air_temperature P1M)', 
                'max(air_temperature P1M)', 
                'min(air_temperature P1M)', 
                'mean(cloud_area_fraction P1M)'            
            ],
            start_time='2014-01-01',
            end_time='2022-12-31')
    weather_df = weather_data_to_dataframe(weater_data)

    merged_df = belysning_df.merge(weather_df, on='year_month', how='left', suffixes=('', '_weather'))
    monthly_avg = merged_df.groupby('year_month').agg({
        'forbruk_kwh': 'mean',
        'mean_air_temp': 'first',
        'cloud_area_fraction': 'first',
        'month': 'first'
    }).reset_index()

    # Remove any NaN values
    monthly_avg = monthly_avg.dropna(subset=['forbruk_kwh', 'mean_air_temp', 'cloud_area_fraction'])
    plot_monthly_average_consumption_vs_weather(monthly_avg, 'mean_air_temp')
    plot_monthly_average_consumption_vs_weather(monthly_avg, 'cloud_area_fraction')

 


if __name__ == "__main__":
    main()