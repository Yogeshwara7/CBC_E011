import ee
import numpy as np
from datetime import datetime

class NDVIProcessor:
    def __init__(self, data_fetcher):
        """Initialize the NDVI processor with a data fetcher."""
        self.data_fetcher = data_fetcher
        self.config = data_fetcher.config
    
    def detect_deforestation(self, ndvi_image):
        """Detect areas with NDVI below threshold."""
        threshold = self.config['alert_threshold']
        deforestation_mask = ndvi_image.lt(threshold)
        return deforestation_mask
    
    def get_statistics(self, ndvi_image):
        """Calculate basic statistics for the NDVI image."""
        stats = ndvi_image.reduceRegion(
            reducer=ee.Reducer.mean().combine(
                reducer2=ee.Reducer.stdDev(),
                sharedInputs=True
            ),
            geometry=self.data_fetcher.get_region(),
            scale=30,
            maxPixels=1e9
        )
        return stats
    
    def process_time_series(self):
        """Process NDVI time series for the region."""
        collection = self.data_fetcher.fetch_satellite_data()
        
        def process_image(image):
            ndvi = self.data_fetcher.calculate_ndvi(image)
            date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
            mean_ndvi = ndvi.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=self.data_fetcher.get_region(),
                scale=30
            ).get('NDVI')
            return ee.Feature(None, {
                'date': date,
                'NDVI': mean_ndvi
            })
        
        ndvi_collection = collection.map(process_image)
        return ndvi_collection 