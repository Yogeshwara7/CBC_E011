import streamlit as st
import requests
import os
from dotenv import load_dotenv
from streamlit_folium import folium_static
from src.ai_analysis import GeminiAnalyzer

load_dotenv()
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

def get_place_suggestions(input_text):
    """Get place suggestions from Google Places API"""
    if not input_text:
        return []
    
    url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    params = {
        "input": input_text,
        "key": GOOGLE_API_KEY,
        "types": "geocode",
        "language": "en"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return []
        data = response.json()
        if data.get("status") != "OK":
            return []
        return data.get("predictions", [])
    except Exception as e:
        st.error(f"Error fetching place suggestions: {str(e)}")
        return []

def render_custom_css():
    """Add custom CSS for better styling"""
    st.markdown("""
        <style>
        /* Main container */
        .main {
            background-color: #f5f5f5;
            padding: 2rem;
        }
        
        /* Headers */
        h1, h2, h3 {
            color: #1E88E5;
            font-weight: 600;
        }
        
        /* Buttons */
        .stButton>button {
            background-color: #1E88E5;
            color: white;
            font-weight: 500;
            border-radius: 5px;
            padding: 0.5rem 1rem;
            border: none;
            transition: all 0.3s ease;
        }
        
        .stButton>button:hover {
            background-color: #1565C0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        
        /* Input fields */
        .stTextInput>div>div>input,
        .stDateInput>div>div>input {
            border-radius: 5px;
            border: 1px solid #ddd;
            padding: 0.5rem;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #f0f2f6;
            border-radius: 4px 4px 0 0;
            gap: 1rem;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #1E88E5;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)

def render_header():
    """Render the main header"""
    st.markdown("""
        <h1 style='text-align: center; margin-bottom: 2rem;'>
            🌱 Environmental Monitoring Dashboard
        </h1>
    """, unsafe_allow_html=True)

def render_sidebar_controls():
    """Render the sidebar controls"""
    with st.sidebar:
        st.markdown("### 📍 Location Settings")
        
        # Initialize session state for selected place if not exists
        if 'selected_place' not in st.session_state:
            st.session_state.selected_place = None
        
        # Place input with autocomplete
        place_input = st.text_input(
            "Enter place name",
            key="place_input",
            help="Start typing to see place suggestions"
        )
        
        # Show suggestions if there's input
        if place_input and place_input != st.session_state.selected_place:
            suggestions = get_place_suggestions(place_input)
            if suggestions:
                st.markdown("#### Suggestions:")
                for suggestion in suggestions[:5]:  # Show top 5 suggestions
                    if st.button(
                        suggestion['description'],
                        key=f"suggestion_{suggestion['place_id']}",
                        use_container_width=True
                    ):
                        # Store the selected place in session state
                        st.session_state.selected_place = suggestion['description']
                        st.session_state.selected_place_id = suggestion['place_id']
                        st.rerun()
        
        # Display selected place if exists
        if st.session_state.selected_place:
            st.markdown(f"**Selected Location:** {st.session_state.selected_place}")
            if st.button("Clear Selection", key="clear_place"):
                st.session_state.selected_place = None
                st.session_state.selected_place_id = None
                st.rerun()
        
        st.markdown("### 📅 Date Range")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start date", key="start_date")
        with col2:
            end_date = st.date_input("End date", key="end_date")
        
        st.markdown("### 📊 Forecast Settings")
        forecast_years = st.slider(
            "Forecast years (max 5)",
            min_value=1,
            max_value=5,
            value=3,
            key="sidebar_forecast_years"
        )
        
        st.markdown("---")
        process = st.button("🔄 Process Latest Data", use_container_width=True)
        
        return st.session_state.selected_place, start_date, end_date, forecast_years, process

def render_main_content(ndvi_map, ndvi_stats, time_series_fig, forecast_fig, ai_analysis, region_name):
    st.markdown("## 📊 Results Overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("NDVI Mean", f"{ndvi_stats.get('NDVI_mean', 'N/A'):.3f}" if ndvi_stats and ndvi_stats.get('NDVI_mean') is not None else "N/A")
    col2.metric("NDVI Std Dev", f"{ndvi_stats.get('NDVI_stdDev', 'N/A'):.3f}" if ndvi_stats and ndvi_stats.get('NDVI_stdDev') is not None else "N/A")
    col3.metric("Region", region_name if region_name else "N/A")

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["🗺️ NDVI Map", "📈 Time Series", "🔮 Forecast"])
    with tab1:
        if ndvi_map is not None:
            folium_static(ndvi_map)
        else:
            st.info("No map available.")
    with tab2:
        if time_series_fig is not None:
            st.plotly_chart(time_series_fig, use_container_width=True)
        else:
            st.info("No time series data available.")
    with tab3:
        if forecast_fig is not None:
            st.plotly_chart(forecast_fig, use_container_width=True)
        else:
            st.info("No forecast data available.")

    st.markdown("---")
    st.markdown("## 🤖 AI-Powered Analysis")
    if st.session_state.get('latest_ndvi') is not None and st.session_state.get('latest_config') is not None:
        if st.button("Generate AI Analysis", key="ai_analysis_button"):
            with st.spinner("Analyzing data with Gemini AI..."):
                gemini_analyzer = GeminiAnalyzer()
                analysis = gemini_analyzer.analyze_ndvi_trend(
                    st.session_state['latest_ndvi'],
                    st.session_state['latest_config']['region']
                )
                if analysis['status'] == 'success':
                    st.success("Analysis Complete!")
                    st.write(analysis['analysis'])
                else:
                    st.error(analysis['analysis'])
    elif ai_analysis:
        st.success(ai_analysis)
    else:
        st.info("Run the AI analysis to see insights here.")

    # You can add the PDF download button here if desired
