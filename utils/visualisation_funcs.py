import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import geopandas as gpd
import folium
from branca.colormap import LinearColormap


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

def histogram_per_kategori(dataframe: pd.DataFrame):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    belysining_df = dataframe[dataframe['kategori'] == 'Belysning']
    traffic_df = dataframe[dataframe['kategori'] == 'Trafikkstyring']
    parkering_df = dataframe[dataframe['kategori'] == 'P-automater']
    ladestasjoner_df = dataframe[dataframe['kategori'] == 'Ladestasjoner']
    # Belysning (top left)
    axes[0, 0].hist(belysining_df['forbruk_kwh'].dropna(), bins=50, 
                    color='skyblue', edgecolor='black', alpha=0.7)
    axes[0, 0].set_xlabel('Forbruk (kWh)')
    axes[0, 0].set_ylabel('Antall observasjoner')
    axes[0, 0].set_title('Belysning')
    axes[0, 0].set_xlim(0, 15000)
    axes[0, 0].grid(axis='y', alpha=0.3)

    # Trafikklys (top right)
    axes[0, 1].hist(traffic_df['forbruk_kwh'].dropna(), bins=100, 
                    color='orange', edgecolor='black', alpha=0.7)
    axes[0, 1].set_xlabel('Forbruk (kWh)')
    axes[0, 1].set_ylabel('Antall observasjoner')
    axes[0, 1].set_title('Trafikklys')
    axes[0, 1].set_xlim(0, 15000)
    axes[0, 1].grid(axis='y', alpha=0.3)

    # Parkering (bottom left)
    axes[1, 0].hist(parkering_df['forbruk_kwh'].dropna(), bins=100, 
                    color='green', edgecolor='black', alpha=0.7)
    axes[1, 0].set_xlabel('Forbruk (kWh)')
    axes[1, 0].set_ylabel('Antall observasjoner')
    axes[1, 0].set_title('Parkering')
    axes[1, 0].set_xlim(0, 15000)
    axes[1, 0].grid(axis='y', alpha=0.3)

    # Ladestasjoner (bottom right)
    axes[1, 1].hist(ladestasjoner_df['forbruk_kwh'].dropna(), bins=100, 
                    color='red', edgecolor='black', alpha=0.7)
    axes[1, 1].set_xlabel('Forbruk (kWh)')
    axes[1, 1].set_ylabel('Antall observasjoner')
    axes[1, 1].set_title('Ladestasjoner')
    axes[1, 1].set_xlim(0, 15000)
    axes[1, 1].grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.show()

def boxplot_per_kategori_per_month(dataframe: pd.DataFrame):
    # Legg til måned-kolonne
    dataframe['month'] = pd.to_datetime(dataframe['dato']).dt.month
    dataframe['month_name'] = pd.to_datetime(dataframe['dato']).dt.strftime('%b')
    
    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    categories = [
        ('Belysning', 'skyblue'),
        ('Trafikkstyring', 'orange'),
        ('P-automater', 'green'),
        ('Ladestasjoner', 'red')
    ]
    
    for idx, (category, color) in enumerate(categories):
        row = idx // 2
        col = idx % 2
        
        category_df = dataframe[dataframe['kategori'] == category]
        
        # Boxplot per måned
        sns.boxplot(data=category_df, x='month_name', y='forbruk_kwh', 
                    order=month_order, ax=axes[row, col], color=color)
        
        axes[row, col].set_xlabel('Måned', fontsize=11, fontweight='bold')
        axes[row, col].set_ylabel('Forbruk (kWh)', fontsize=11, fontweight='bold')
        axes[row, col].set_title(f'{category} - Forbruk per måned', 
                                 fontsize=12, fontweight='bold')
        axes[row, col].tick_params(axis='x', rotation=45)
        axes[row, col].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.show()

def create_barplot_percent_total_observations_category(dataframe: pd.DataFrame):
    count_by_kategori = dataframe['kategori'].value_counts()
    count_by_kategori_percent = (count_by_kategori / len(dataframe)) * 100
    count_by_kategori_percent = count_by_kategori_percent.sort_values(ascending=False)

    # Create a nice plot
    fig, ax = plt.subplots(figsize=(14, 8))

    # Create bars with color gradient
    colors = plt.cm.viridis(range(len(count_by_kategori_percent)))
    bars = ax.bar(range(len(count_by_kategori_percent)), 
                count_by_kategori_percent.values,
                color=colors,
                edgecolor='black',
                linewidth=0.5,
                alpha=0.8)

    # Add percentage labels on top of bars
    for i, (bar, value) in enumerate(zip(bars, count_by_kategori_percent.values)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{value:.1f}%',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Customize the plot
    ax.set_xticks(range(len(count_by_kategori_percent)))
    ax.set_xticklabels(count_by_kategori_percent.index, 
                        rotation=45,           # <-- Roterer labels
                        ha='right',            # <-- Høyre-justert
                        fontsize=10)

    ax.set_xlabel('Kategori', fontsize=12, fontweight='bold')
    ax.set_ylabel('Prosent av målinger (%)', fontsize=12, fontweight='bold')
    ax.set_title('Prosent av Målinger per Kategori', fontsize=14, fontweight='bold', pad=20)

    # Add grid for easier reading
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_axisbelow(True)

    # Add a horizontal line at 5%
    ax.axhline(y=5, color='red', linestyle='--', linewidth=2, label='5% grense', alpha=0.7)
    ax.legend(loc='upper right', fontsize=10)

    # Set y-axis to show percentages nicely
    ax.set_ylim(0, max(count_by_kategori_percent.values) * 1.1)

    plt.tight_layout()
    plt.savefig('kategori_prosent_bar.png', dpi=300, bbox_inches='tight')
    plt.show()