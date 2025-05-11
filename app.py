import streamlit as st
import ee
from src.data_fetcher import DataFetcher
from src.ndvi_processor import NDVIProcessor
from src.visualization import Visualizer
import folium
from streamlit_folium import folium_static
import os
import sys           
from src.ai_analysis import GeminiAnalyzer
import requests
from dotenv import load_dotenv
import datetime
from src.ui_components import (
    render_custom_css,
    render_header,
    render_sidebar_controls,
    render_main_content
)
from datetime import datetime, timedelta
import plotly.io as pio
from fpdf import FPDF
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import box

# Windows-specific setup
if sys.platform == 'win32':
    # Suppress Windows-specific warnings
    import warnings
    warnings.filterwarnings('ignore', category=UserWarning)
    
    # Set environment variable for Earth Engine
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Set Earth Engine token file
os.environ['EARTHENGINE_TOKEN_FILE'] = r'C:\Users\Yoghana BK\.config\earthengine\credentials'

load_dotenv()  # take environment variables from .env.
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

def geocode_place(place_name):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": place_name,
        "format": "json",
        "limit": 1
    }
    response = requests.get(url, params=params)
    results = response.json()
    if results:
        lat = float(results[0]['lat'])
        lon = float(results[0]['lon'])
        display_name = results[0]['display_name']
        return lat, lon, display_name
    else:
        return None, None, None

def google_places_autocomplete(input_text):
    url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    params = {
        "input": input_text,
        "key": GOOGLE_API_KEY,
        "types": "geocode",
        "language": "en"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return []
        data = response.json()
        if data.get("status") != "OK":
            return []
        return data.get("predictions", [])
    except Exception as e:
        return []

def google_geocode(place_id):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "place_id": place_id,
        "key": GOOGLE_API_KEY
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return None, None, None
        data = response.json()
        if data.get("status") != "OK":
            return None, None, None
        results = data.get("results", [])
        if results:
            location = results[0]['geometry']['location']
            display_name = results[0]['formatted_address']
            return location['lat'], location['lng'], display_name
        else:
            return None, None, None
    except Exception as e:
        return None, None, None

def get_place_coordinates(place_id):
    """Get coordinates for a place using Google Places API"""
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "place_id": place_id,
        "key": GOOGLE_API_KEY
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return None, None, None
        data = response.json()
        if data.get("status") != "OK":
            return None, None, None
        results = data.get("results", [])
        if results:
            location = results[0]['geometry']['location']
            display_name = results[0]['formatted_address']
            return location['lat'], location['lng'], display_name
        return None, None, None
    except Exception as e:
        st.error(f"Error getting place coordinates: {str(e)}")
        return None, None, None

def create_pdf(region, date_range, ndvi_mean, ndvi_std, map_path, ts_path, forecast_path):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 12, "Environmental Monitoring Report", ln=True, align='C')
    pdf.ln(8)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Region: {region}", ln=True)
    pdf.cell(0, 10, f"Date Range: {date_range}", ln=True)
    pdf.cell(0, 10, f"NDVI Mean: {ndvi_mean}", ln=True)
    pdf.cell(0, 10, f"NDVI Std Dev: {ndvi_std}", ln=True)
    pdf.ln(8)

    # NDVI Map
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "NDVI Map", ln=True)
    pdf.image(map_path, x=30, w=150)
    pdf.ln(8)

    # NDVI Time Series
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "NDVI Time Series", ln=True)
    pdf.image(ts_path, x=30, w=150)
    pdf.ln(8)

    # NDVI Forecast
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "NDVI Forecast (Past & Next 5 Years)", ln=True)
    pdf.image(forecast_path, x=30, w=150)
    pdf.ln(8)

    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 10, "This report was generated automatically by the Environmental Monitoring System.")
    return pdf.output(dest='S').encode('latin-1')

def main():
    # Set Streamlit to wide mode for a modern dashboard look
    st.set_page_config(page_title="Environmental Monitoring Dashboard", layout="wide")

    # Add custom CSS and header
    render_custom_css()
    render_header()

    # Get controls from sidebar
    selected_place, start_date, end_date, forecast_years, process = render_sidebar_controls()

    # Use session state for region, fallback to config if not set
    if 'region' in st.session_state:
        region = st.session_state['region']
    else:
        import json
        with open('config/config.json', 'r') as f:
            config = json.load(f)
        region = config['region']
        if 'name' not in region:
            region['name'] = "Default Region"

    # Initialize data handlers
    data_fetcher = DataFetcher(region=region)
    ndvi_processor = NDVIProcessor(data_fetcher)
    visualizer = Visualizer(data_fetcher)
    gemini_analyzer = GeminiAnalyzer()

    # Use session state to persist NDVI collection
    if 'ndvi_collection' not in st.session_state:
        st.session_state['ndvi_collection'] = None

    if process:
        with st.spinner("Processing data..."):
            try:
                # If a place is selected, get its coordinates
                if 'selected_place_id' in st.session_state and st.session_state.selected_place_id:
                    lat, lon, display_name = get_place_coordinates(st.session_state.selected_place_id)
                    if lat and lon:
                        st.session_state['region'] = {
                            'name': display_name,
                            'coordinates': {
                                'north': lat + 0.05,
                                'south': lat - 0.05,
                                'east': lon + 0.05,
                                'west': lon - 0.05
                            }
                        }
                        data_fetcher = DataFetcher(region=st.session_state['region'])
                        ndvi_processor = NDVIProcessor(data_fetcher)
                        visualizer = Visualizer(data_fetcher)

                # Get the latest image
                collection = data_fetcher.fetch_satellite_data(
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d")
                )

                if collection.size().getInfo() == 0:
                    st.error("No satellite images found for the selected region and time period")
                    return

                latest_image = ee.Image(collection.first())
                ndvi = data_fetcher.calculate_ndvi(latest_image)
                st.session_state['latest_ndvi'] = ndvi
                st.session_state['latest_config'] = data_fetcher.config

                stats = ndvi_processor.get_statistics(ndvi)
                st.session_state['ndvi_stats'] = stats

                ndvi_collection = ndvi_processor.process_time_series()
                st.session_state['ndvi_collection'] = ndvi_collection

                m = visualizer.create_map(ndvi)
                st.session_state['map'] = m

                # Save your Plotly figures
                fig_time_series = visualizer.plot_time_series(ndvi_collection)
                fig_forecast = visualizer.plot_forecast(ndvi_collection, periods=60)
                fig_time_series.write_image("time_series.png")
                fig_forecast.write_image("forecast.png")

            except Exception as e:
                st.error(f"Error processing data: {str(e)}")

    # Sidebar: Show configuration
    st.sidebar.header("Current Configuration")
    if 'selected_place' in st.session_state and st.session_state.selected_place:
        st.sidebar.markdown(f"**Selected Place:** {st.session_state.selected_place}")
    st.sidebar.json(data_fetcher.config)

    # Prepare variables for main content
    region_name = (
        st.session_state['latest_config']['region']['name']
        if st.session_state.get('latest_config') and st.session_state['latest_config'].get('region') and st.session_state['latest_config']['region'].get('name')
        else "N/A"
    )
    ndvi_stats = st.session_state.get('ndvi_stats')
    # These will be used in the PDF section
    ndvi_mean = ndvi_stats['NDVI_mean'] if ndvi_stats and ndvi_stats.get('NDVI_mean') is not None else "N/A"
    ndvi_std = ndvi_stats['NDVI_stdDev'] if ndvi_stats and ndvi_stats.get('NDVI_stdDev') is not None else "N/A"
    map_path = "ndvi_map.png"
    ts_path = "time_series.png"
    forecast_path = "forecast.png"
    date_range = f"{start_date} to {end_date}"

    # Render main content (dashboard style)
    render_main_content(
        ndvi_map=st.session_state.get('map'),
        ndvi_stats=ndvi_stats,
        time_series_fig=visualizer.plot_time_series(st.session_state.get('ndvi_collection')) if st.session_state.get('ndvi_collection') else None,
        forecast_fig=visualizer.plot_forecast(st.session_state.get('ndvi_collection'), periods=forecast_years*12) if st.session_state.get('ndvi_collection') else None,
        ai_analysis=st.session_state.get('ai_analysis'),
        region_name=region_name
    )

    # PDF Report Download Section
    st.markdown("---")
    st.markdown("### 📄 Download PDF Report")
    if st.button("Generate PDF Report"):
        # Save a static map if needed (replace with your actual map saving logic)
        # fig_map = ... (create or get your map figure)
        # fig_map.write_image("ndvi_map.png")
        pdf_bytes = create_pdf(region_name, date_range, ndvi_mean, ndvi_std, map_path, ts_path, forecast_path)
        st.download_button(
            label="Download PDF",
            data=pdf_bytes,
            file_name=f"{region_name}_environmental_report.pdf",
            mime="application/pdf"
        )

if __name__ == "__main__":
    main() 