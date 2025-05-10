# Environmental Monitoring System

A modular Python project for monitoring environmental changes using satellite data from Google Earth Engine.

## Setup Instructions

### 1. Google Earth Engine Setup
1. Go to [Google Earth Engine Signup](https://earthengine.google.com/signup/)
2. Sign in with your Google account
3. Fill out the registration form
4. Wait for approval (usually takes 1-2 business days)

### 2. Python Environment Setup
1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Earth Engine Authentication
1. Install the Earth Engine CLI:
   ```bash
   pip install earthengine-api
   ```

2. Authenticate with Earth Engine:
   ```bash
   earthengine authenticate
   ```

3. Follow the browser prompts to complete authentication

## Project Structure

## Usage
1. Configure your monitoring parameters in `config/config.json`
2. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

## Configuration
Edit `config/config.json` to specify:
- Use case type
- Region coordinates
- Date range
- Index type
- Alert thresholds
