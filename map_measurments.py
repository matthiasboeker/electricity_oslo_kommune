import json
import pandas as pd
import geopandas as gpd
import folium
import topojson as tp
from pathlib import Path

TOP_CATEGORIES = [
    "Belysning",
    "Trafikkstyring",
    "P-automater",
    "Ladestasjoner",
]

CATEGORY_COLORS = {
    "Belysning": "#1f77b4",        
    "Trafikkstyring": "#ff7f0e",   
    "P-automater": "#2ca02c",      
    "Ladestasjoner": "#d62728",   
}

def load_bydeler_geodata(topojson_path: Path) -> gpd.GeoDataFrame:
    """Load Oslo bydeler from TopoJSON into a GeoDataFrame."""
    with open(topojson_path, "r", encoding="utf-8") as f:
        topo_data = json.load(f)

    topology = tp.Topology(topo_data, object_name="Bydeler")
    gdf = topology.to_gdf()
    gdf = gdf.set_crs("EPSG:4326", allow_override=True)

    return gdf


def load_and_prepare_electricity_data(csv_path: Path) -> pd.DataFrame:
    """Load electricity data and aggregate by unique location and category."""
    df = pd.read_csv(csv_path, engine="python")

    df = df[df["kategori"].isin(TOP_CATEGORIES)].copy()
    df = df.dropna(subset=["latitude", "longitude"])

    df_locations = (
        df.groupby(["addresse", "kategori", "latitude", "longitude"])
        .agg({"forbruk_kwh": "mean"})
        .reset_index()
    )

    return df_locations

def create_base_map() -> folium.Map:
    """Create a Folium base map centered on Oslo."""
    return folium.Map(
        location=[59.9139, 10.7522],
        zoom_start=11,
        tiles="CartoDB positron",
    )


def add_bydeler_layer(m: folium.Map, gdf: gpd.GeoDataFrame) -> None:
    """Add bydeler boundaries to the map."""
    folium.GeoJson(
        gdf,
        style_function=lambda feature: {
            "fillColor": "none",
            "color": "#333333",
            "weight": 2,
            "fillOpacity": 0,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["BYDELSNAVN"],
            aliases=["Bydel:"],
            localize=True,
        ),
    ).add_to(m)


def add_location_markers(
    m: folium.Map,
    df_locations: pd.DataFrame,
    category_colors: dict,
) -> None:
    """Add CircleMarkers for each electricity location."""
    for _, row in df_locations.iterrows():
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=4,
            popup=(
                f"<b>{row['addresse']}</b><br>"
                f"Kategori: {row['kategori']}<br>"
                f"Gj.snitt forbruk: {row['forbruk_kwh']:.0f} kWh"
            ),
            tooltip=row["kategori"],
            color=category_colors[row["kategori"]],
            fill=True,
            fillColor=category_colors[row["kategori"]],
            fillOpacity=0.7,
            weight=1,
        ).add_to(m)


def add_legend(
    m: folium.Map,
    df_locations: pd.DataFrame,
    category_colors: dict,
) -> None:
    """Add a fixed HTML legend showing category counts."""
    legend_html = """
    <div style="position: fixed;
                top: 10px; right: 10px; width: 180px;
                background-color: white; z-index:9999; font-size:14px;
                border:2px solid grey; border-radius: 5px; padding: 10px">
    <p style="margin-bottom: 10px; font-weight: bold;">Kategorier</p>
    """

    for category, color in category_colors.items():
        count = len(df_locations[df_locations["kategori"] == category])
        legend_html += f"""
        <p style="margin: 5px 0;">
            <span style="background-color:{color};
                         width: 15px; height: 15px;
                         display: inline-block; margin-right: 5px;
                         border-radius: 50%;"></span>
            {category} ({count})
        </p>
        """

    legend_html += "</div>"
    m.get_root().html.add_child(folium.Element(legend_html))

def main() -> None:
    path_to_topjson = Path(__file__).parent /  "data" / "Bydeler_Oslo_m_marka.json"
    path_to_electricity_file = Path(__file__).parent / "data" / "stromforbruk_with_bydel.csv"
    path_to_store_map = Path(__file__).parent / "map_visualisations" / "oslo_electricity_map.html"
    gdf_bydeler = load_bydeler_geodata(path_to_topjson)

    print("Loading electricity data...")
    df_locations = load_and_prepare_electricity_data(path_to_electricity_file)

    print(f"Plotting {len(df_locations)} unique locations")

    m = create_base_map()
    add_bydeler_layer(m, gdf_bydeler)
    add_location_markers(m, df_locations, CATEGORY_COLORS)
    add_legend(m, df_locations, CATEGORY_COLORS)

    m.save(path_to_store_map)

if __name__ == "__main__":
    main()