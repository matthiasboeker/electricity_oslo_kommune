from pathlib import Path
import json
import geopandas as gpd
import topojson as tp
import pandas as pd 
import numpy as np  
from scipy.stats import pearsonr
import matplotlib.pyplot as plt
from typing import Tuple
from exploratory_analysis import remove_negative_values, clean_data_from_outliers

import folium
from branca.colormap import LinearColormap


def create_average_map(
    bydel_gdf: gpd.GeoDataFrame,
    avg_df: pd.DataFrame,
    output_path: str = "average_map.html"
):
    """Create choropleth map showing average lighting energy usage per bydel."""

    # Merge geodata with average data
    gdf = bydel_gdf.merge(
        avg_df,
        left_on="BYDELSNAVN",
        right_on="Bydel",
        how="left"
    )

    # Create map centered on Oslo
    m = folium.Map(
        location=[59.9139, 10.7522],
        zoom_start=11,
        tiles="CartoDB positron"
    )

    # Colormap (low = light, high = dark)
    vmin = gdf["forbruk_kwh"].min()
    vmax = gdf["forbruk_kwh"].max()

    colormap = LinearColormap(
        colors=["#edf8fb", "#b2e2e2", "#66c2a4", "#238b45"],
        vmin=vmin,
        vmax=vmax,
        caption="Gjennomsnittlig forbruk (kWh)"
    )

    # Add choropleth
    folium.GeoJson(
        gdf,
        style_function=lambda feature: {
            "fillColor": colormap(feature["properties"]["forbruk_kwh"])
            if feature["properties"].get("forbruk_kwh") is not None
            else "lightgray",
            "color": "black",
            "weight": 1.5,
            "fillOpacity": 0.75,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["BYDELSNAVN", "forbruk_kwh"],
            aliases=["Bydel:", "Gjennomsnittlig forbruk (kWh):"],
            localize=True,
            labels=True,
        ),
    ).add_to(m)

    colormap.add_to(m)

    # Title
    title_html = """
    <div style="position: fixed;
                top: 10px; left: 50px; width: 420px;
                background-color: white; border:2px solid grey;
                z-index:9999; font-size:14px; padding: 10px">
        <h4 style="margin:0;">Gjennomsnittlig forbruk ladestasjoner per bydel</h4>
        <p style="margin:5px 0;">Mørkere farge = høyere forbruk</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))

    m.save(output_path)
    print(f"✓ Average usage map saved: {output_path}")



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
    

def plot_forbruk_by_bydel_over_time(aggregated_df: pd.DataFrame):
    bydeler = sorted(aggregated_df["Bydel"].unique())
    colors = plt.cm.tab20(np.linspace(0, 1, len(bydeler)))
    # alternatives: tab20b, tab20c, viridis, plasma

    plt.figure(figsize=(16, 9))

    for color, bydel in zip(colors, bydeler):
        grp = aggregated_df[aggregated_df["Bydel"] == bydel].sort_values("year")
        plt.plot(
            grp["year"],
            grp["forbruk_kwh"],
            label=bydel,
            color=color,
            linewidth=2,
            alpha=0.9
        )

    plt.title("Strømforbruk til belysning per bydel (2014–2022)", fontsize=16)
    plt.xlabel("År")
    plt.ylabel("Strømforbruk (kWh)")
    plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)

    plt.legend(
        title="Bydel",
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        frameon=False,
        fontsize=10
    )

    plt.tight_layout()
    plt.show()


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
    print(avg_by_year)
    create_average_map(bydel_gdf, avg_by_year)


if __name__ == "__main__":
    main()