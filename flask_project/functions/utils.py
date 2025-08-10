import requests
import os
from datetime import datetime
import google.generativeai as genai #Google Gemini API
import aiohttp
import asyncio

NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
NOMINATIM_NEARBY_URL = "https://nominatim.openstreetmap.org/search"
# Remove or comment out the Google Places API URL
# GOOGLE_PLACES_API_URL = "https://maps.googleapis.com/maps/..."

OPENWEATHERMAP_API_URL = "https://api.openweathermap.org/data/2.5/forecast"
PLACE_DETAILS_API_URL = 'https://maps.googleapis.com/maps/api/place/details/json'
GOOGLE_GEMINI_API_KEY = genai.configure(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))


async def fetch_nominatim_suggestions(search_term, limit=5):
    """Fetches places of worship for all religions based on the location name asynchronously."""
    print(f"Searching for: {search_term}")  # Debug log
    
    params = {
        'q': search_term,
        'format': 'json',
        'limit': 10,  # Fetch more results to filter properly
        'accept-language': 'en'
    }
    
    headers = {
        'User-Agent': 'PilgrimPlanner/1.0 (ralphaacarvalho@gmail.com)'
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(NOMINATIM_BASE_URL, params=params, headers=headers) as response:
                response.raise_for_status()
                results = await response.json()
                
                filtered_results = []
                search_term_lower = search_term.lower()
                
                # Keywords to identify places of worship
                worship_keywords = ["temple", "church", "mosque", "synagogue", "basilica", "gurdwara", 
                                    "cathedral", "shrine", "monastery", "asram", "stupa", "mandir"," "]
                
                for place in results:
                    display_name = place.get('display_name', '')
                    name = place.get('name', '')

                    # Check if the place name or description contains religious keywords
                    if any(keyword in display_name.lower() or keyword in name.lower() for keyword in worship_keywords):
                        filtered_place = {
                            'display_name': display_name,
                            'lat': place.get('lat'),
                            'lon': place.get('lon')
                        }
                        filtered_results.append(filtered_place)
                
                return filtered_results[:limit]
                
        except aiohttp.ClientError as e:
            print(f"Error during Nominatim API call: {e}")
            return []

# To call the async function
def get_nominatim_suggestions(search_term, limit=5):
    return asyncio.run(fetch_nominatim_suggestions(search_term, limit))

def get_nearby_places(latitude, longitude, search_type, radius=5000):
    """Fetches nearby places using Nominatim API."""
    print(f"DEBUG: Searching for {search_type} near ({latitude}, {longitude})")
    
    try:
        # Convert coordinates
        lat = float(latitude)
        lon = float(longitude)
        
        # Define search parameters
        params = {
            'format': 'json',
            'limit': 50,
            'accept-language': 'en',
            'viewbox': f"{lon-0.1},{lat-0.1},{lon+0.1},{lat+0.1}",
            'bounded': 1,
        }
        
        # Add category based on search type
        if search_type == 'hotel':
            params['amenity'] = 'hotel'  # Search amenity
        elif search_type == 'tourist_attraction':
            params['tourism'] = 'attraction'
        elif search_type == 'restaurant':
            params['amenity'] = 'restaurant'
        elif search_type == 'cafe':
            params['amenity'] = 'cafe'
        elif search_type == 'museum':
            params['tourism'] = 'museum'
        elif search_type == 'historical_site':
            params['historic'] = 'yes'
        else:
            params['amenity'] = search_type
            
        headers = {
            'User-Agent': 'PilgrimPlanner/1.0 (ralphaacarvalho@gmail.com)'  # Use your email
        }
        
        print(f"DEBUG: Making request with params: {params}")
        
        response = requests.get(
            NOMINATIM_BASE_URL,
            params=params,
            headers=headers,
            timeout=30
        )
        
        print(f"DEBUG: Response status: {response.status_code}")
        response.raise_for_status()
        
        results = response.json()
        print(f"DEBUG: Found {len(results)} raw results")
        
        places = []
        for place in results:
            place_lat = float(place.get('lat', 0))
            place_lon = float(place.get('lon', 0))
            
            # Calculate distance
            from math import cos, sqrt, pi
            dx = 111.32 * cos(lat * pi/180) * (place_lon - lon)
            dy = 111.32 * (place_lat - lat)
            distance = sqrt(dx * dx + dy * dy) * 1000  # Convert to meters
            
            if distance <= radius:
                place_data = {
                    'name': place.get('name', place.get('display_name', '')).split(',')[0],
                    'full_address': place.get('display_name', ''),
                    'lat': place_lat,
                    'lon': place_lon,
                    'type': search_type,
                    'distance': int(distance),
                    'osm_type': place.get('type', ''),
                    'category': place.get('class', ''),
                    'price': place.get('price', 'N/A')  # Add price field
                }
                places.append(place_data)
                print(f"DEBUG: Added place: {place_data['name']} ({place_data['distance']}m)")
        
        # Sort by distance
        places.sort(key=lambda x: x['distance'])
        return places
        
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Request failed: {str(e)}")
        return []
    except ValueError as e:
        print(f"ERROR: Invalid coordinates: {str(e)}")
        return []
    except Exception as e:
        print(f"ERROR: Unexpected error: {str(e)}")
        return []
    
    
def get_weather(latitude, longitude, start_date_str, end_date_str):
    """Fetches weather information for the specified dates using Open-Meteo API."""
    
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    
    # Open-Meteo API URL
    OPEN_METEO_API_URL = "https://api.open-meteo.com/v1/forecast"
    
    # For simplicity, we only get weather for the very first date
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'hourly': 'temperature_2m,weathercode',
        'timezone': 'auto'
    }
    
    try:
        response = requests.get(OPEN_METEO_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Map weather codes to Font Awesome icons
        weather_code_to_icon = {
            0: 'sun',  # Clear sky
            1: 'cloud-sun',  # Mainly clear
            2: 'cloud',  # Partly cloudy
            3: 'cloud',  # Overcast
            45: 'smog',  # Fog
            48: 'smog',  # Depositing rime fog
            51: 'cloud-rain',  # Drizzle: Light
            53: 'cloud-rain',  # Drizzle: Moderate
            55: 'cloud-rain',  # Drizzle: Dense intensity
            56: 'cloud-rain',  # Freezing Drizzle: Light
            57: 'cloud-rain',  # Freezing Drizzle: Dense intensity
            61: 'cloud-showers-heavy',  # Rain: Slight
            63: 'cloud-showers-heavy',  # Rain: Moderate
            65: 'cloud-showers-heavy',  # Rain: Heavy intensity
            66: 'cloud-showers-heavy',  # Freezing Rain: Light
            67: 'cloud-showers-heavy',  # Freezing Rain: Heavy intensity
            71: 'snowflake',  # Snow fall: Slight
            73: 'snowflake',  # Snow fall: Moderate
            75: 'snowflake',  # Snow fall: Heavy intensity
            77: 'snowflake',  # Snow grains
            80: 'cloud-showers-heavy',  # Rain showers: Slight
            81: 'cloud-showers-heavy',  # Rain showers: Moderate
            82: 'cloud-showers-heavy',  # Rain showers: Violent
            85: 'snowflake',  # Snow showers slight
            86: 'snowflake',  # Snow showers heavy
            95: 'bolt',  # Thunderstorm: Slight or moderate
            96: 'bolt',  # Thunderstorm with slight hail
            99: 'bolt'  # Thunderstorm with heavy hail
        }
        
        weather_code = data['hourly']['weathercode'][0]
        weather_info = {
            'temperature': data['hourly']['temperature_2m'][0],  # Get the first hour's temperature
            'description': weather_code,  # Get the first hour's weather code
            'icon': weather_code_to_icon.get(weather_code, 'cloud')  # Default to 'cloud' if code not found
        }
        return weather_info
    except requests.exceptions.RequestException as e:
        print(f"Error during Open-Meteo API call: {e}")
        return None

import re

def generate_gemini_text(location_name, start_date_str, end_date_str):
    """Generates text using Gemini API."""

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

        prompt = f"""
Provide concise and helpful information for travelers planning a trip to {location_name}
from {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}. Include:

   Necessary Precautions: (e.g., vaccinations, safety tips, visa requirements)
   Local Customs: (e.g., greetings, dining etiquette, dress code)
   Must-See Attractions: (e.g. iconic monuments, historical sites, recommended tours)
   Other Relevant Information: (e.g., currency exchange, transportation tips, language basics)
give it in raw HTML code. NO MARKDOWN SYNTAX ALLOWED
"""
        # Ensure the API key is set
        api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Google Gemini API key is not set")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        print(f"DEBUG: Sending prompt to Gemini API: {prompt}")  # Debug log
        response = model.generate_content(prompt)
        
        print(f"DEBUG: Received response from Gemini API: {response.text}")  # Debug log
        
        # Remove triple backticks and the word "html"
        clean_text = re.sub(r'```html|```|', '', response.text)
        
        return clean_text
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "Could not generate information at this time. Please try again later."

def calculate_estimated_cost(travelers, num_days, accommodation_cost_per_night=100,  transport_cost=200, daily_cost_per_person = 75):
    """Provides a very basic cost estimation.  This should be refined."""
    accommodation_cost = accommodation_cost_per_night * num_days
    food_cost = daily_cost_per_person * num_days * travelers
    total_cost = accommodation_cost + transport_cost + food_cost
    return total_cost

def get_place_details(place_id):
    """Fetches detailed information about a place using Google Places API."""
 #get your API key
    api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
    params = {
        'place_id': place_id,
        'fields': 'name,formatted_address,rating,photos,reviews',  # Specify fields
        'key': api_key
    }
    try:
        response = requests.get(PLACE_DETAILS_API_URL, params=params)
        response.raise_for_status()
        return response.json().get('result', {})  # Return empty dict if 'result' is missing
    except requests.exceptions.RequestException as e:
        print(f"Error during Google Places API call: {e}")
        return {}  # Or handle the error as needed.


def generate_itinerary(destination, start_date, end_date, travelers, accommodation, transportation, reason_for_visiting, all_places, estimated_cost, weather_info, notes):
    """
    Generates an itinerary for the visit focusing on the reason for the visit using Gemini API.
    """
    prompt = f"""
    Create a comprehensive travel itinerary for a trip to {destination} from {start_date} to {end_date} for {travelers} travelers. The itinerary should be structured around the primary reason for the visit: {reason_for_visiting}, ensuring activities and locations align with this purpose.

    Include details on:

    Accommodation: {accommodation}
    Transportation: {transportation}
    A day-by-day schedule that starts with arrival and ends with departure, incorporating relevant sightseeing, activities, and experiences that enhance the trip's purpose.
    Key places to visit: {all_places}
    Estimated total cost: ${estimated_cost:.2f}
    Weather conditions and travel considerations: {weather_info}
    Additional notes and special considerations: {notes}
    Ensure the itinerary maintains a balance between structured activities and free time while keeping the primary reason for the visit at the center of the experience.
    give response in Raw HTML code. NO MARKDOWN SYNTAX ALLOWED
    """
    
    try:
        # Ensure the API key is set
        api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Google Gemini API key is not set")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        print(f"DEBUG: Sending prompt to Gemini API: {prompt}")  # Debug log
        response = model.generate_content(prompt)
        
        print(f"DEBUG: Received response from Gemini API: {response.text}")  # Debug log
        
        # Remove triple backticks and the word "html"
        clean_text = re.sub(r'```html|```|', '', response.text)
        
        return clean_text
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "Could not generate itinerary at this time. Please try again later."