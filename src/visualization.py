import folium
import ee
import streamlit as st
import plotly.express as px
import pandas as pd
import os
import sys
import plotly.graph_objects as go
from prophet import Prophet

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
                'palette': ['brown', 'red', 'yellow', 'lightgreen', 'green']
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
            
            # Get the collection info
            collection_info = ndvi_collection.getInfo()
            
            # Process each image in the collection
            for feature in collection_info['features']:
                date = feature['properties']['date']
                value = feature['properties']['NDVI']
                dates.append(date)
                values.append(value)
            
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
    
    def plot_forecast(self, ndvi_collection, periods=60):
        """
        Plot NDVI time series and forecast for the next 'periods' months.
        """
        try:
            # Extract dates and NDVI values
            dates = []
            values = []
            collection_info = ndvi_collection.getInfo()
            
            for feature in collection_info['features']:
                if feature['properties']['NDVI'] is not None:
                    dates.append(feature['properties']['date'])
                    values.append(feature['properties']['NDVI'])

            # Prepare DataFrame for Prophet
            df = pd.DataFrame({'ds': dates, 'y': values})
            df['ds'] = pd.to_datetime(df['ds'])

            # Fit Prophet model
            model = Prophet()
            model.fit(df)

            # Make future dataframe (next 5 years, monthly)
            future = model.make_future_dataframe(periods=periods, freq='ME')
            forecast = model.predict(future)

            # Plot
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['ds'], y=df['y'], mode='lines', name='Historical NDVI'))
            fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='Forecast NDVI'))
            fig.update_layout(title='NDVI Forecast (Past & Next 5 Years)', xaxis_title='Date', yaxis_title='NDVI')
            return fig
        except Exception as e:
            print(f"Error in forecast plotting: {str(e)}")
            raise 