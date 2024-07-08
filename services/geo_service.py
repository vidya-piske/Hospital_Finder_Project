import os
from flask import Blueprint, request, jsonify
import requests
from dotenv import load_dotenv
from utils import summarize_hospitals

# Load environment variables from .env file
load_dotenv()

geo_service_app = Blueprint('geo_service_app', __name__)

@geo_service_app.route('/location', methods=["POST"])
def get_property_details():
    data = request.get_json()
    location = data.get('location')

    # Check if location is provided and in the correct format
    if not location or ',' not in location:
        return jsonify({"error": "Invalid location format. Please provide latitude and longitude separated by comma."}), 400

    # Get the API keys from environment variables
    google_api_key = os.getenv('GOOGLE_API_KEY')
    open_api_key = os.getenv('OPENAI_API_KEY')

    if not google_api_key or not open_api_key:
        return jsonify({"error": "API keys are not set properly."}), 500

    TYPE = "hospital"
    radius = 500

    # Construct the URL for the nearby search request
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius={radius}&type={TYPE}&key={google_api_key}"

    # Make the request to the Google Places API
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch data from Google API"}), response.status_code

    places = response.json().get('results', [])

    # Check if the places list is empty
    if not places:
        return jsonify({"error": "No hospitals found within the specified radius."}), 404

    # Initialize a list to hold detailed information about each hospital
    hospital_details = []

    # Fetch details for up to 5 hospitals
    for place in places[:5]:
        place_id = place.get('place_id')
        detail_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,formatted_address,formatted_phone_number,website,rating,reviews&key={google_api_key}"
        detail_response = requests.get(detail_url)

        # Check if details request was successful
        if detail_response.status_code == 200:
            detail = detail_response.json().get('result', {})
            hospital_details.append(detail)
        else:
            print(f"Failed to fetch details for place_id {place_id}: {detail_response.status_code}")

    # Sort hospitals by rating and return the top 5 (redundant since we're already limiting to 5)
    hospital_details = sorted(hospital_details, key=lambda x: x.get('rating', 0), reverse=True)

    # Summarize the hospital details using OpenAI
    summary = summarize_hospitals(open_api_key, hospital_details)

    return jsonify({"hospital_details": hospital_details, "summary": summary})
