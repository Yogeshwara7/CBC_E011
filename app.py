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

def main():
    st.title("Environmental Monitoring System")
    
    # Place name input
    st.sidebar.header("Location Search")
    query = st.sidebar.text_input("Search for a place (Google Autocomplete):")
    suggestions = []
    if query and len(query) > 2:
        suggestions = google_places_autocomplete(query)

    if suggestions:
        place_choice = st.sidebar.selectbox(
            "Select a place:",
            [s['description'] for s in suggestions]
        )
        selected = next(s for s in suggestions if s['description'] == place_choice)
        if st.sidebar.button("Use this place"):
            lat, lon, display_name = google_geocode(selected['place_id'])
            if lat and lon:
                st.sidebar.success(f"Selected: {display_name}")
                region = {
                    "name": display_name,
                    "coordinates": {
                        "north": lat + 0.05,
                        "south": lat - 0.05,
                        "east": lon + 0.05,
                        "west": lon - 0.05
                    }
                }
                st.session_state['region'] = region
            else:
                st.sidebar.error("Could not fetch coordinates for this place.")

    # Use session state for region, fallback to config if not set
    if 'region' in st.session_state:
        region = st.session_state['region']
    else:
        # fallback to config file
        import json
        with open('config/config.json', 'r') as f:
            config = json.load(f)
        region = config['region']

    # Now, when initializing DataFetcher, pass the region
    data_fetcher = DataFetcher(region=region)
    ndvi_processor = NDVIProcessor(data_fetcher)
    visualizer = Visualizer(data_fetcher)
    gemini_analyzer = GeminiAnalyzer()
    
    # Use session state to persist NDVI collection
    if 'ndvi_collection' not in st.session_state:
        st.session_state['ndvi_collection'] = None
    
    # Sidebar controls
    st.sidebar.header("Controls")
    st.sidebar.header("Date Range Selection")
    today = datetime.date.today()
    default_start = today.replace(year=today.year - 1, month=1, day=1)
    default_end = today

    start_date = st.sidebar.date_input(
        "Start date", value=default_start, max_value=default_end, key="start_date"
    )
    end_date = st.sidebar.date_input(
        "End date", value=default_end, min_value=start_date, max_value=today, key="end_date"
    )

    if st.sidebar.button("Process Latest Data"):
        with st.spinner("Processing data..."):
            try:
                # Get the latest image
                collection = data_fetcher.fetch_satellite_data(
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d")
                )
                latest_image = ee.Image(collection.first())
                
                # Calculate NDVI
                ndvi = data_fetcher.calculate_ndvi(latest_image)
                
                # Create map
                m = visualizer.create_map(ndvi)
                
                
                # Show statistics
                stats = ndvi_processor.get_statistics(ndvi)
            
                
                # Process and store NDVI time series in session state
                ndvi_collection = ndvi_processor.process_time_series()
                st.session_state['ndvi_collection'] = ndvi_collection
                
                # Store NDVI and config in session state
                st.session_state['latest_ndvi'] = ndvi
                st.session_state['latest_config'] = data_fetcher.config
                st.session_state['map'] = m
                st.session_state['ndvi_stats'] = stats.getInfo()
            except Exception as e:
                st.error(f"Error processing data: {str(e)}")
    
    # Display configuration
    st.sidebar.header("Current Configuration")
    st.sidebar.json(data_fetcher.config)
    
    # Show map if available
    if st.session_state.get('map') is not None:
        st.write("NDVI Map")
        folium_static(st.session_state['map'])

    # Show NDVI statistics if available
    if st.session_state.get('ndvi_stats') is not None:
        st.write("NDVI Statistics:", st.session_state['ndvi_stats'])

    # Show time series if available
    if st.session_state.get('ndvi_collection') is not None:
        st.write("NDVI Time Series")
        fig = visualizer.plot_time_series(st.session_state['ndvi_collection'])
        st.plotly_chart(fig, key="ndvi_time_series_chart")

        if st.button("Show NDVI Forecast (Next 5 Years)"):
            with st.spinner("Forecasting NDVI..."):
                try:
                    fig_forecast = visualizer.plot_forecast(st.session_state['ndvi_collection'], periods=60)
                    st.plotly_chart(fig_forecast, key="ndvi_forecast_chart")
                except Exception as e:
                    st.error(f"Error generating forecast: {str(e)}")
    
    display_ai_analysis()
    
    for key in ['ndvi_collection', 'latest_ndvi', 'latest_config', 'map', 'ndvi_stats']:
        if key not in st.session_state:
            st.session_state[key] = None

    st.sidebar.header("Forecast Options")
    forecast_years = st.sidebar.slider(
        "Forecast years (max 5)", min_value=1, max_value=5, value=3, key="forecast_years"
    )

def display_ai_analysis():
    st.subheader("AI-Powered Analysis")
    if st.session_state.get('latest_ndvi') is not None and st.session_state.get('latest_config') is not None:
        if st.button("Generate AI Analysis"):
            with st.spinner("Analyzing data with Gemini AI..."):
                gemini_analyzer = GeminiAnalyzer()
                analysis = gemini_analyzer.analyze_ndvi_trend(
                    st.session_state['latest_ndvi'],
                    st.session_state['latest_config']['region']
                )
                if analysis['status'] == 'success':
                    st.success("Analysis Complete!")
                    st.write(analysis['analysis'])
                else:
                    st.error(analysis['analysis'])
    else:
        st.info("Please process latest data first to enable AI analysis.")

if __name__ == "__main__":
    main() 