import ee
import json
from datetime import datetime
import pandas as pd
import os
import sys

class DataFetcher:
    def __init__(self, config_path='config/config.json'):
        """Initialize the DataFetcher with configuration."""
        self.config = self._load_config(config_path)
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
                ee.Initialize()
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
    
    def fetch_satellite_data(self):
        """Fetch satellite data based on configuration."""
        try:
            region = self.get_region()
            start_date = self.config['date_range']['start_date']
            end_date = self.config['date_range']['end_date']
            
            # Get the satellite collection
            collection = ee.ImageCollection(self.config['satellite']) \
                .filterBounds(region) \
                .filterDate(start_date, end_date) \
                .filter(ee.Filter.lt('CLOUD_COVER', self.config['cloud_cover_threshold']))
            
            return collection
        except Exception as e:
            print(f"Error fetching satellite data: {str(e)}")
            raise
    
    def calculate_ndvi(self, image):
        """Calculate NDVI for a given image."""
        try:
            nir = image.select('B5')
            red = image.select('B4')
            
            ndvi = image.normalizedDifference(['B5', 'B4']).rename('NDVI')
            return ndvi
        except Exception as e:
            print(f"Error calculating NDVI: {str(e)}")
            raise 