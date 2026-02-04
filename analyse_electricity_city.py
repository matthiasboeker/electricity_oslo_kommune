from pathlib import Path
import json
import geopandas as gpd
import topojson as tp
import pandas as pd 
import numpy as np  
from scipy.stats import pearsonr
import matplotlib.pyplot as plt
from typing import Tuple
from utils.transformations import remove_negative_values, clean_data_from_outliers
from utils.loading_funcs import read_csv_data, load_bydeler_geodata
from utils.visualisation_funcs import plot_forbruk_by_bydel_over_time, create_average_map


def prepare_electricity_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and prepare electricity data."""
    df = remove_negative_values(df)
    df = clean_data_from_outliers(df)
    df.dropna(subset=['BYDEL'], inplace=True)
    
    df['dato'] = pd.to_datetime(df['dato'])
    df['year'] = df['dato'].dt.year

    return df


def aggregate_consumption_by_bydel_year(df: pd.DataFrame, kategori: str) -> pd.DataFrame:
    kategori_df = df[df['kategori'] == kategori].copy()
    kategori_agg = kategori_df.groupby(['BYDELSNAVN', 'year']).agg({
        'forbruk_kwh': 'sum'
    }).reset_index()
    kategori_agg.columns = ['Bydel', 'year', 'forbruk_kwh']
    return kategori_agg


def main():
    """Main analysis pipeline."""
    # Define paths
    base_path = Path(__file__).parent
    path_to_electricity = base_path / 'data' / 'stromforbruk_with_bydel.csv'
    path_to_bydel = base_path / 'data' / 'Bydeler_Oslo_m_marka.json'
    
    # Load data
    electricity_df = read_csv_data(path_to_electricity, sep=',')
    bydel_gdf = load_bydeler_geodata(path_to_bydel)

    # Prepare data
    electricity_df = prepare_electricity_data(electricity_df)
    belysning_agg = aggregate_consumption_by_bydel_year(electricity_df, "Belysning")
    plot_forbruk_by_bydel_over_time(belysning_agg)

    ladestasjoner_agg = aggregate_consumption_by_bydel_year(electricity_df, "Ladestasjoner")
    avg_by_year = (
        ladestasjoner_agg
        .groupby("Bydel", as_index=False)["forbruk_kwh"]
        .mean()
    )
    create_average_map(bydel_gdf, avg_by_year)


if __name__ == "__main__":
    main()