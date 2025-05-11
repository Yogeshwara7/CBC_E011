import ee
import json
from datetime import datetime
import pandas as pd
import os
import sys
import streamlit as st

class DataFetcher:
    def __init__(self, config_path='config/config.json', region=None):
        """Initialize the DataFetcher with configuration."""
        self.config = self._load_config(config_path)
        if region is not None:
            self.config['region'] = region
        self._initialize_ee()
        
    def _load_config(self, config_path):
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {str(e)}")
            raise
        
    def _initialize_ee(self):
        """Initialize Earth Engine API with Windows-specific handling."""
        try:
            if not ee.data._initialized:
                ee.Initialize(project='chromatic-being-459406-m1')
        except Exception as e:
            print("Please authenticate with Earth Engine first using 'earthengine authenticate'")
            raise e
    
    def get_region(self):
        """Convert config coordinates to Earth Engine geometry."""
        coords = self.config['region']['coordinates']
        return ee.Geometry.Rectangle([
            coords['west'], coords['south'],
            coords['east'], coords['north']
        ])
    
    def fetch_satellite_data(self, start_date=None, end_date=None):
        """Fetch satellite data based on configuration or provided dates."""
        try:
            region = self.get_region()
            # Use provided dates if given, else fall back to config
            if start_date is None:
                start_date = self.config['date_range']['start_date']
            if end_date is None:
                end_date = self.config['date_range']['end_date']

            collection = ee.ImageCollection(self.config['satellite']) \
                .filterBounds(region) \
                .filterDate(start_date, end_date) \
                .filter(ee.Filter.lt('CLOUD_COVER', self.config['cloud_cover_threshold']))
            
            # Add validation
            count = collection.size().getInfo()
            if count == 0:
                raise ValueError(f"No satellite images found for the selected region and time period. Try adjusting the date range or cloud cover threshold.")
            
            print(f"Found {count} images in collection")
            return collection
        except Exception as e:
            print(f"Error fetching satellite data: {str(e)}")
            raise
    
    def calculate_ndvi(self, image):
        """Calculate NDVI for a given image."""
        try:
            # Calculate NDVI using Earth Engine's normalizedDifference
            ndvi = image.normalizedDifference(['B5', 'B4']).rename('NDVI')
            
            # Add a mask to remove invalid values
            ndvi = ndvi.updateMask(ndvi.gt(-1).And(ndvi.lt(1)))
            
            return ndvi
        except Exception as e:
            print(f"Error calculating NDVI: {str(e)}")
            raise

    def update_region(self, region):
        """Update the region configuration."""
        self.config['region'] = region

if 'region' in st.session_state:
    region = st.session_state['region']
else:
    import json
    with open('config/config.json', 'r') as f:
        config = json.load(f)
    region = config['region']

data_fetcher = DataFetcher(region=region) 