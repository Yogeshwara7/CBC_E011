import ee
import webbrowser
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

def authenticate():
    """Authenticate with Google Earth Engine using OAuth2."""
    try:
        # Try to initialize Earth Engine
        ee.Authenticate()
        ee.Initialize(project='my-project')
        print("Already authenticated!")
        return True
    except:
        try:
            # Start the authentication flow
            ee.Authenticate()
            ee.Initialize()
            print("Authentication successful!")
            return True
        except Exception as e:
            print(f"Authentication failed: {str(e)}")
            return False

if __name__ == "__main__":
    authenticate()