import yaml
import json
import os

def load_config():
    """
    Load configuration from either YAML or JSON file
    """
    # Try to load from YAML first
    yaml_path = os.path.join('config', 'settings.yaml')
    if os.path.exists(yaml_path):
        with open(yaml_path, 'r') as f:
            return yaml.safe_load(f)
    
    # Fallback to JSON
    json_path = os.path.join('config', 'config.json')
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            return json.load(f)
    
    raise FileNotFoundError("No configuration file found in config directory")

def load_config():
    return {
        'gemini': {
            'api_key': 'AIzaSyD5_XGDYTwIlRkDqSZAk003I_3ceCH64lQ'  # Make sure this is set
        }
    }
