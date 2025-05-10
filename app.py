import streamlit as st
import ee
from src.data_fetcher import DataFetcher
from src.ndvi_processor import NDVIProcessor
from src.visualization import Visualizer
import folium
from streamlit_folium import folium_static
import os
import sys

# Windows-specific setup
if sys.platform == 'win32':
    # Suppress Windows-specific warnings
    import warnings
    warnings.filterwarnings('ignore', category=UserWarning)
    
    # Set environment variable for Earth Engine
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Set Earth Engine token file
os.environ['EARTHENGINE_TOKEN_FILE'] = r'C:\Users\Yoghana BK\.config\earthengine\credentials'

def main():
    st.title("Environmental Monitoring System")
    
    # Initialize components
    try:
        # Initialize Earth Engine with Windows-specific settings
        if not ee.data._initialized:
            ee.Initialize(project='chromatic-being-459406-m1')
        
        data_fetcher = DataFetcher()
        ndvi_processor = NDVIProcessor(data_fetcher)
        visualizer = Visualizer(data_fetcher)
        
        # Sidebar controls
        st.sidebar.header("Controls")
        if st.sidebar.button("Process Latest Data"):
            with st.spinner("Processing data..."):
                try:
                    # Get the latest image
                    collection = data_fetcher.fetch_satellite_data()
                    latest_image = ee.Image(collection.first())
                    
                    # Calculate NDVI
                    ndvi = data_fetcher.calculate_ndvi(latest_image)
                    
                    # Create map
                    m = visualizer.create_map(ndvi)
                    folium_static(m)
                    
                    # Show statistics
                    stats = ndvi_processor.get_statistics(ndvi)
                    st.write("NDVI Statistics:", stats.getInfo())
                    
                    # Show time series
                    st.write("NDVI Time Series")
                    ndvi_collection = ndvi_processor.process_time_series()
                    fig = visualizer.plot_time_series(ndvi_collection)
                    st.plotly_chart(fig)
                except Exception as e:
                    st.error(f"Error processing data: {str(e)}")
        
        # Display configuration
        st.sidebar.header("Current Configuration")
        st.sidebar.json(data_fetcher.config)
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.info("Please make sure you have authenticated with Google Earth Engine using 'earthengine authenticate'")

if __name__ == "__main__":
    main() 