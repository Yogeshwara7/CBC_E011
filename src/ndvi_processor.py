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
        try:
            region = self.data_fetcher.get_region()
            
            # Calculate mean and stdDev separately
            mean = ndvi_image.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=30,
                maxPixels=1e9
            )
            
            stdDev = ndvi_image.reduceRegion(
                reducer=ee.Reducer.stdDev(),
                geometry=region,
                scale=30,
                maxPixels=1e9
            )
            
            # Get the results
            mean_info = mean.getInfo()
            stdDev_info = stdDev.getInfo()
            
            return {
                'NDVI_mean': mean_info.get('NDVI'),
                'NDVI_stdDev': stdDev_info.get('NDVI')
            }
        except Exception as e:
            print(f"Error calculating statistics: {str(e)}")
            raise
    
    def process_time_series(self):
        """Process NDVI time series for the region."""
        try:
            collection = self.data_fetcher.fetch_satellite_data()
            
            def process_image(image):
                # Calculate NDVI
                ndvi = self.data_fetcher.calculate_ndvi(image)
                
                # Get the date
                date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
                
                # Calculate mean NDVI for the region
                mean_ndvi = ndvi.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=self.data_fetcher.get_region(),
                    scale=30,
                    maxPixels=1e9
                ).get('NDVI')
                
                # Create a feature with the date and NDVI value
                return ee.Feature(None, {
                    'date': date,
                    'NDVI': mean_ndvi
                })
            
            # Map the function over the collection
            ndvi_collection = collection.map(process_image)
            
            return ndvi_collection
        except Exception as e:
            print(f"Error processing time series: {str(e)}")
            raise 