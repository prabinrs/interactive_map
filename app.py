# Import necessary libraries
import streamlit as st
import folium
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from streamlit_folium import folium_static
from io import BytesIO
import base64

# --- 1. Set up the Streamlit page ---
st.set_page_config(
    page_title="Aki's Interactive Map with Data Visualization",
    layout="wide",
)

st.title("🗺️ Aki's Interactive Map with Health Data")
st.markdown("Upload your country data (CSV) to visualize health metrics on an interactive map.")
st.markdown("---")

# --- 2. Create a sample data file for demonstration ---
@st.cache_data
def get_sample_data():
    """Generates a sample DataFrame for demonstration."""
    data = {
        'country': ['India', 'Pakistan', 'Nepal', 'Bangladesh', 'Uganda', 'Ethiopia', 'Kenya', 'Tanzania', 'DRC', 'Rwanda'],
        'Cardiovascular': [10, 5, 3, 7, 1, 0, 0, 0, 0, 0],
        'Child Health': [4, 6, 2, 5, 1, 1, 3, 0, 0, 0],
        'Respiratory': [3, 2, 4, 3, 2, 3, 2, 4, 2, 0],
        'Maternal Health': [0, 0, 0, 0, 0, 0, 0, 1, 0, 2],
        'Neonatal Health': [0, 0, 0, 0, 0, 1, 0, 1, 0, 1],
        'Other': [0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
    }
    return pd.DataFrame(data)

sample_df = get_sample_data()

st.download_button(
    label="Download Sample Data CSV",
    data=sample_df.to_csv(index=False).encode('utf-8'),
    file_name='sample_country_data.csv',
    mime='text/csv',
)
st.markdown("---")

# --- 3. File uploader and data processing ---
uploaded_file = st.file_uploader("Upload your data file (CSV format)", type=["csv"])

if uploaded_file:
    # Read the uploaded data
    user_df = pd.read_csv(uploaded_file)
    st.write("Uploaded Data:")
    st.dataframe(user_df)

    # --- 4. Load World GeoJSON data ---
    world_geojson_url = 'https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson'
    try:
        world_gdf = gpd.read_file(world_geojson_url)
    except Exception as e:
        st.error(f"Error loading GeoJSON data: {e}")
        st.stop()

    # --- 5. Merge user data with GeoDataFrame ---
    # We'll use a lowercase country name for a more robust merge
    user_df['country'] = user_df['country'].str.strip().str.capitalize()
    world_gdf['name'] = world_gdf['name'].str.strip().str.capitalize()
    
    merged_gdf = world_gdf.merge(user_df, left_on='name', right_on='country', how='left')

    # Drop rows without geometries or data
    merged_gdf = merged_gdf.dropna(subset=['geometry'])

    # --- 6. Create the Folium map ---
    # Centered on a reasonable global location
    m = folium.Map(location=[25, 80], zoom_start=4, tiles='cartodb positron')

    # Get the columns that represent health metrics
    metric_cols = [col for col in user_df.columns if col != 'country']
    colors = ['seagreen', 'royalblue', 'orange', 'pink', 'lime', 'darkblue']
    color_dict = {metric_cols[i]: colors[i] for i in range(len(metric_cols))}

    # Add countries to the map
    folium.GeoJson(
        merged_gdf,
        name='countries',
        style_function=lambda x: {
            # Check if there is data for this country to change its color
            'fillColor': 'red' if not pd.isna(x['properties'].get(metric_cols[0])) else 'grey',
            'color': 'white',
            'weight': 1,
            'fillOpacity': 0.7
        },
        tooltip=folium.GeoJsonTooltip(fields=['name']),
    ).add_to(m)

    # --- 7. Create and embed matplotlib charts in popups ---
    for _, row in merged_gdf.iterrows():
        country_name = row['name']
        
        # Check if the country has data
        if not pd.isna(row.get(metric_cols[0])):
            # Get data for the current country
            country_data = row[metric_cols].to_frame().T
            
            # Create the matplotlib plot
            fig, ax = plt.subplots(figsize=(3, 2), dpi=100)
            country_data.plot(
                kind='bar', 
                stacked=True, 
                ax=ax, 
                legend=False, 
                rot=0, 
                width=0.8, 
                color=[color_dict.get(col) for col in metric_cols]
            )
            #ax.set_title(f"Health Data for {country_name}", fontsize=10)
            ax.set_xlabel("")
            ax.set_ylabel("")
            ax.set_xticklabels(['']) # Hide x-axis labels as it's a single bar
            #ax.legend(title="Category", fontsize=6, loc='center left', bbox_to_anchor=(1, 0.5))
            # FIX: Explicitly remove the legend if it exists
            if ax.get_legend() is not None:
                ax.get_legend().remove()

            # FIX: Hide the y-axis
            ax.yaxis.set_visible(False)
            
            # FIX: Hide the plot outlines (spines)
            for spine in ax.spines.values():
                spine.set_visible(False)

            plt.tight_layout()
            
            # Save the plot to a BytesIO object (in memory)
            buffer = BytesIO()
            fig.savefig(buffer, format='png', transparent=True)
            plt.close(fig)
            
            # Encode the image to base64
            base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Create the HTML for the popup
           # html_popup = f"""
           # <div style="text-align: center;">
            #    <img src="data:image/png;base64,{base64_image}" width="100%">
            #</div>
            #"""
            
            # Create the popup object
            #popup = folium.Popup(html_popup, max_width=250)
          
            # Add a marker at the centroid with the popup
            # Check for valid geometry before adding marker
            """if row['geometry'].is_valid and not row['geometry'].is_empty:
                folium.Marker(
                    location=[row['geometry'].centroid.y, row['geometry'].centroid.x],
                    popup=popup,
                    tooltip=country_name,
                    icon=folium.Icon(color='red', icon='info-sign')
                ).add_to(m)"""
            
            # ------- 
             # Create the HTML for the DivIcon
            html_icon = f"""
            <img src="data:image/png;base64,{base64_image}" style="width: 60px; height: 100px;">
            """
             # Create the DivIcon
            div_icon = folium.DivIcon(
                icon_size=(60, 100),
                icon_anchor=(30, 80),
                html=html_icon
            )
            
            # Add a marker at the centroid with the DivIcon
            # Check for valid geometry before adding marker
            if row['geometry'].is_valid and not row['geometry'].is_empty:
                folium.Marker(
                    location=[row['geometry'].centroid.y, row['geometry'].centroid.x],
                    icon=div_icon,
                    tooltip=country_name,
                ).add_to(m)


            # -----

    # --- 8. Display the map in Streamlit ---
    st.subheader("Interactive Map")
    folium_static(m,height=800, width=1024)

     # --- 9. Create and display a separate legend in the bottom-right corner ---
    legend_patches = [mpatches.Patch(color=color_dict[col], label=col) for col in metric_cols]
    fig, ax = plt.subplots(figsize=(4, 2), facecolor='white')
    ax.legend(handles=legend_patches, loc='center', ncol=2, title="Categories")
    ax.axis('off')

    legend_buffer = BytesIO()
    fig.savefig(legend_buffer, format='png', transparent=True)
    plt.close(fig)
    legend_base64 = base64.b64encode(legend_buffer.getvalue()).decode('utf-8')

    st.markdown(
        f"""
        <div style="position: fixed; bottom: 10px; right: 10px; z-index: 9999;">
            <img src="data:image/png;base64,{legend_base64}" alt="Legend" style="width: 250px; border: 1px solid #ccc; background-color: #fff; padding: 5px;">
        </div>
        """,
        unsafe_allow_html=True
    )

else:
    st.info("Please upload a CSV file to begin.")

