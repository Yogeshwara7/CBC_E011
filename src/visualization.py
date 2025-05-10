import folium
import ee
import streamlit as st
import plotly.express as px
import pandas as pd
import os
import sys

class Visualizer:
    def __init__(self, data_fetcher):
        """Initialize the visualizer with a data fetcher."""
        self.data_fetcher = data_fetcher
        self.config = data_fetcher.config
    
    def create_map(self, ndvi_image):
        """Create an interactive map with Folium."""
        try:
            # Get the center of the region
            coords = self.config['region']['coordinates']
            center_lat = (coords['north'] + coords['south']) / 2
            center_lon = (coords['east'] + coords['west']) / 2
            
            # Create the map
            m = folium.Map(location=[center_lat, center_lon], zoom_start=10)
            
            # Add NDVI layer
            ndvi_vis = {
                'min': -1,
                'max': 1,
                'palette': ['red', 'yellow', 'green']
            }
            
            map_id = ndvi_image.getMapId(ndvi_vis)
            folium.TileLayer(
                tiles=map_id['tile_fetcher'].url_format,
                attr='Google Earth Engine',
                overlay=True,
                name='NDVI'
            ).add_to(m)
            
            return m
        except Exception as e:
            st.error(f"Error creating map: {str(e)}")
            raise
    
    def plot_time_series(self, ndvi_collection):
        """Create a time series plot using Plotly."""
        try:
            # Convert collection to pandas DataFrame
            dates = []
            values = []
            
            def extract_data(image):
                date = ee.Date(image.get('date')).format('YYYY-MM-dd').getInfo()
                value = image.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=self.data_fetcher.get_region(),
                    scale=30
                ).get('NDVI').getInfo()
                dates.append(date)
                values.append(value)
            
            # Process the collection
            ndvi_collection.getInfo()['features'].map(extract_data)
            
            # Create DataFrame
            df = pd.DataFrame({
                'Date': dates,
                'NDVI': values
            })
            
            # Create plot
            fig = px.line(df, x='Date', y='NDVI', title='NDVI Time Series')
            return fig
        except Exception as e:
            st.error(f"Error creating time series plot: {str(e)}")
            raise 