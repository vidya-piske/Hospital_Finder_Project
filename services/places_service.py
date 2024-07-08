import os
import requests
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
from utils import summarize_hospitals

# Load environment variables from .env file
load_dotenv()

# Initialize Blueprint
places_service_app = Blueprint('places_service_app', __name__)

# Retrieve API keys from environment variables
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Function to fetch hospitals near a location based on place name
def get_hospitals_by_place(place_name):
    # Fetch latitude and longitude from Google Geocoding API based on place name
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={place_name}&key={GOOGLE_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        results = response.json().get('results', [])
        if results:
            location = results[0]['geometry']['location']
            lat, lng = location['lat'], location['lng']
            
            # Fetch hospitals near the retrieved latitude and longitude
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=500&type=hospital&key={GOOGLE_API_KEY}"
            response = requests.get(url)
            if response.status_code == 200:
                hospitals = response.json().get('results', [])
                if hospitals:
                    hospital_details = []
                    # Limit the loop to 5 iterations
                    for hospital in hospitals[:5]:
                        place_id = hospital.get('place_id')
                        details = get_hospital_details(place_id)
                        if details:
                            hospital_details.append(details)
                    
                    # Sort hospitals by rating and select the top 5
                    hospital_details = sorted(hospital_details, key=lambda x: x.get('rating', 0), reverse=True)[:5]
                    
                    # Summarize hospital details using OpenAI API
                    summary = summarize_hospitals(OPENAI_API_KEY, hospital_details)
                    
                    return {"hospital_details": hospital_details, "summary": summary}
                else:
                    return {"error": "No hospitals found near the specified location"}
            else:
                return {"error": "Failed to fetch hospitals from Google API"}
        else:
            return {"error": "Failed to get location from Google Geocoding API"}
    else:
        return {"error": "Failed to fetch location data from Google API"}

# Function to fetch detailed information about a hospital
def get_hospital_details(place_id):
    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,formatted_address,formatted_phone_number,website,rating,reviews&key={GOOGLE_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('result', {})
    return {}

# Route to handle POST requests for place names
@places_service_app.route('/place', methods=["POST"])
def handle_place_request():
    data = request.get_json()
    place_name = data.get('place_name')

    if not place_name:
        return jsonify({"error": "Place name is required"}), 400

    # Call function to get hospitals by place name
    result = get_hospitals_by_place(place_name)

    return jsonify(result)

