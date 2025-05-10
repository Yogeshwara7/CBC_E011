import google.generativeai as genai
from config.settings import load_config

class GeminiAnalyzer:
    def __init__(self):
        config = load_config()
        self.api_key = config.get('gemini', {}).get('api_key')
        if not self.api_key:
            raise ValueError("Gemini API key not found in configuration")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def analyze_ndvi_trend(self, ndvi_data, location_info):
        """
        Analyze NDVI trends using Gemini AI
        
        Args:
            ndvi_data (dict): NDVI data with timestamps and values
            location_info (dict): Location information including coordinates
            
        Returns:
            dict: Analysis results including insights and recommendations
        """
        prompt = f"""
        Analyze the following NDVI (Normalized Difference Vegetation Index) data for {location_info['name']}:
        
        Location: {location_info['name']}
        Coordinates: {location_info['coordinates']}
        NDVI Data: {ndvi_data}
        
        Please provide:
        1. Trend analysis
        2. Potential environmental implications
        3. Recommendations for monitoring
        """
        
        try:
            response = self.model.generate_content(prompt)
            return {
                'analysis': response.text,
                'status': 'success'
            }
        except Exception as e:
            return {
                'analysis': f"Error in AI analysis: {str(e)}",
                'status': 'error'
            }
    
    def generate_insights(self, ndvi_data, weather_data=None):
        """
        Generate insights combining NDVI and weather data
        
        Args:
            ndvi_data (dict): NDVI data
            weather_data (dict, optional): Weather data if available
            
        Returns:
            dict: Generated insights
        """
        prompt = f"""
        Analyze the following environmental data:
        
        NDVI Data: {ndvi_data}
        Weather Data: {weather_data if weather_data else 'Not available'}
        
        Please provide:
        1. Key environmental changes
        2. Potential causes
        3. Impact assessment
        4. Recommendations
        """
        
        try:
            response = self.model.generate_content(prompt)
            return {
                'insights': response.text,
                'status': 'success'
            }
        except Exception as e:
            return {
                'insights': f"Error generating insights: {str(e)}",
                'status': 'error'
            }
