import pdfkit
import io
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response
from dotenv import load_dotenv
from datetime import datetime
from models import db, Trip
from functions.forms import DestinationForm, DatesForm, AccommodationForm, TransportationForm, PlacesOfInterestForm, LoginForm, SignupForm
from functions.utils import get_nominatim_suggestions, get_nearby_places, get_weather, generate_gemini_text, calculate_estimated_cost, get_place_details, generate_itinerary
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import json
import os
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import User

# Load environment variables from .env file
load_dotenv()

# Get the path to the wkhtmltopdf executable from environment variables
wkhtmltopdf_path = os.getenv('WKHTMLTOPDF_PATH', r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")

# Specify the path to the wkhtmltopdf executable
config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')  # Use a strong, random key in production
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///travel_planner.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # to suppress the warning
db.init_app(app)

# Create database tables within the application context
with app.app_context():
    db.create_all()

# Initialize Flask-Migrate
from flask_migrate import Migrate
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Global variables to hold the form data across routes.
destination_data = {}
dates_data = {}
accommodation_data = {}
transportation_data = {}
places_of_interest_data = {}

@app.route('/', methods=['GET', 'POST'])
def index():
    form = DestinationForm()
    suggestions = []
    if form.validate_on_submit():
        destination_data['destination_name'] = form.destination.data
        destination_data['latitude'] = form.latitude.data
        destination_data['longitude'] = form.longitude.data
        destination_data['display_name'] = form.display_name.data
        return redirect(url_for('dates'))

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':  # Handle the autosuggest functionality
        search_term = request.form.get('destination')
        if search_term:
            suggestions = get_nominatim_suggestions(search_term)
            return jsonify(suggestions)  # Return suggestions as JSON
    return render_template('index.html', form=form, suggestions=suggestions)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = SignupForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists', 'danger')
            return render_template('signup.html', form=form)
        
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dates', methods=['GET', 'POST'])
def dates():
    form = DatesForm()  # Changed from AccommodationForm to DatesForm
    if form.validate_on_submit():
        dates_data['start_date'] = form.start_date.data
        dates_data['end_date'] = form.end_date.data
        dates_data['num_travelers'] = form.num_travelers.data
        return redirect(url_for('accommodation'))  # Redirect to accommodation page
    return render_template('dates.html', form=form)

@app.route('/accommodation', methods=['GET', 'POST'])
@login_required
def accommodation():
    form = AccommodationForm()
    accommodations = []
    if destination_data.get('latitude') and destination_data.get('longitude'):
        # Convert coordinates to float
        lat = float(destination_data['latitude'])
        lon = float(destination_data['longitude'])
        print(f"Searching for accommodations near: {lat}, {lon}")  # Debug log
        
        accommodations = get_nearby_places(
            latitude=lat,
            longitude=lon,
            search_type='hotel',
            radius=5000  # 5km radius
        )
        print(f"Found {len(accommodations)} accommodations")  # Debug log
        
    if form.validate_on_submit():
        accommodation_data['accommodation_name'] = form.accommodation.data
        accommodation_data['accommodation_details'] = form.accommodation_details.data
        return redirect(url_for('place_information'))
    return render_template('accommodation.html', form=form, accommodations=accommodations)

@app.route('/place_information', methods=['GET', 'POST'])
@login_required
def place_information():
    # Note: implemented for faster load. It is better to call again the APIs.
    destination_name = destination_data.get('destination_name', 'Unknown')
    start_date = dates_data.get('start_date', datetime.now()).strftime('%Y-%m-%d')
    end_date = dates_data.get('end_date', datetime.now()).strftime('%Y-%m-%d')

    weather = get_weather(destination_data['latitude'], destination_data['longitude'], start_date, end_date)
    gemini_text = generate_gemini_text(destination_name, start_date, end_date)  # This call to Gemini is too expensive. It needs to be managed carefully.

    return render_template(
        'place_information.html',
        accommodation_name=accommodation_data.get('accommodation_name', 'Unknown'),
        accommodation_details=accommodation_data.get('accommodation_details', 'No details'),
        weather=weather,
        gemini_text=gemini_text,
        destination_name=destination_name,
        start_date=start_date,
        end_date=end_date
    )

@app.route('/transportation', methods=['GET', 'POST'])
@login_required
def transportation():
    form = TransportationForm()
    if form.validate_on_submit():
        transportation_data['transportation_method'] = form.transportation_method.data
        # Add this line to save the reason_for_visiting
        transportation_data['reason_for_visiting'] = form.reason_for_visiting.data
        return redirect(url_for('places_of_interest'))
    return render_template('transportation.html', form=form)

@app.route('/places_of_interest', methods=['GET', 'POST'])
@login_required
def places_of_interest():
    form = PlacesOfInterestForm()
    interests = []
    if destination_data.get('latitude') and destination_data.get('longitude'):
        # Fetch restaurants, cafes, museums, and historical sites
        restaurants = get_nearby_places(
            destination_data['latitude'], 
            destination_data['longitude'], 
            search_type='restaurant',
            radius=4000  # 7km radius
        )
        cafes = get_nearby_places(
            destination_data['latitude'], 
            destination_data['longitude'], 
            search_type='cafe',
            radius=4000  # 7km radius
        )
        museums = get_nearby_places(
            destination_data['latitude'], 
            destination_data['longitude'], 
            search_type='museum',
            radius=4000  # 7km radius
        )
        historical_sites = get_nearby_places(
            destination_data['latitude'], 
            destination_data['longitude'], 
            search_type='historical_site',
            radius=4000  # 7km radius
        )
        interests = restaurants + cafes + museums + historical_sites  # Combine the results

        # Save all places of interest along with their distances
        places_of_interest_data['all_places'] = interests

    if form.validate_on_submit():
        places_of_interest_data['selected_places'] = form.places.data  # This is a list of strings. You need to handle it in the form rendering. See the forms.py
        return redirect(url_for('confirmation'))
    return render_template('places_of_interest.html', form=form, interests=interests, destination_data=destination_data)

@app.route('/confirmation', methods=['GET', 'POST'])
@login_required
def confirmation():
    if request.method == 'POST':
        # Fetch weather information
        weather_info = get_weather(
            destination_data.get('latitude'),
            destination_data.get('longitude'),
            dates_data.get('start_date').strftime('%Y-%m-%d'),
            dates_data.get('end_date').strftime('%Y-%m-%d')
        )
        
        # Serialize weather_info to JSON string
        weather_info_json = json.dumps(weather_info)

        # Save trip details to the database
        trip = Trip(
            user_id=current_user.id,  # Add the user_id
            destination=destination_data.get('destination_name'),
            latitude=destination_data.get('latitude'),
            longitude=destination_data.get('longitude'),
            start_date=dates_data.get('start_date'),
            end_date=dates_data.get('end_date'),
            travelers=dates_data.get('num_travelers'),
            accommodation=accommodation_data.get('accommodation_name'),
            transportation=','.join(transportation_data.get('transportation_method', [])),
            reason_for_visiting=transportation_data.get('reason_for_visiting'),  # Changed from request.form.get()
            places_of_interest=','.join(places_of_interest_data.get('selected_places', [])),
            all_places=json.dumps(places_of_interest_data.get('all_places', [])),  # Save all places of interest as JSON
            gemini_info=generate_gemini_text(destination_data.get('destination_name'), dates_data.get('start_date').strftime('%Y-%m-%d'), dates_data.get('end_date').strftime('%Y-%m-%d')),
            estimated_cost=calculate_estimated_cost(dates_data.get('num_travelers'), (dates_data.get('end_date') - dates_data.get('start_date')).days),
            weather_info=weather_info_json,  # Save weather_info as JSON string
            notes=request.form.get('notes')
        )
        db.session.add(trip)
        db.session.commit()
        flash('Trip saved successfully!', 'success')
        return redirect(url_for('past_submissions'))

    # Calculate total cost (replace with your actual logic)
    estimated_cost = calculate_estimated_cost(dates_data.get('num_travelers'), (dates_data.get('end_date') - dates_data.get('start_date')).days)
    return render_template(
        'confirmation.html',
        destination=destination_data,
        dates=dates_data,
        accommodation=accommodation_data,
        transportation=transportation_data,
        interests=places_of_interest_data,
        estimated_cost=estimated_cost
    )

@app.route('/past_submissions', methods=['GET'])
@login_required
def past_submissions():
    trips = Trip.query.filter_by(user_id=current_user.id).order_by(Trip.start_date.desc()).all()
    return render_template('past_submissions.html', trips=trips)

@app.route('/generate_latest_trip_pdf/<int:trip_id>', methods=['GET'])
def generate_latest_trip_pdf(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    
    # Render the HTML content
    rendered_html = render_template(
        'trip_template.html',
        trip=trip,
        destination=trip.destination,
        start_date=trip.start_date.strftime('%Y-%m-%d'),
        end_date=trip.end_date.strftime('%Y-%m-%d'),
        travelers=trip.travelers,
        accommodation=trip.accommodation,
        transportation=trip.transportation,
        reason_for_visiting=trip.reason_for_visiting,
        all_places=json.loads(trip.all_places),
        estimated_cost=trip.estimated_cost,
        weather_info=json.loads(trip.weather_info),
        notes=trip.notes,
        gemini_info=trip.gemini_info
    )
    
    # Convert the rendered HTML to PDF
    pdf = pdfkit.from_string(rendered_html, False, configuration=config)
    
    # Send the PDF as a response
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=latest_trip_{trip_id}.pdf'
    
    return response

@app.route('/generate_latest_trip_itinerary_pdf_with_gemini/<int:trip_id>', methods=['GET'])
def generate_latest_trip_itinerary_pdf_with_gemini(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    
    # Render the HTML content
    rendered_html = generate_itinerary(
        destination=trip.destination,
        start_date=trip.start_date.strftime('%Y-%m-%d'),
        end_date=trip.end_date.strftime('%Y-%m-%d'),
        travelers=trip.travelers,
        accommodation=trip.accommodation,
        transportation=trip.transportation,
        reason_for_visiting=trip.reason_for_visiting,
        all_places=trip.all_places,
        estimated_cost=trip.estimated_cost,
        weather_info=trip.weather_info,
        notes=trip.notes
    )
    
    # Convert the rendered HTML to PDF
    pdf = pdfkit.from_string(rendered_html, False, configuration=config)
    
    # Send the PDF as a response
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=trip_itinerary_{trip_id}.pdf'
    
    return response
if __name__ == '__main__':
    app.run(debug=True)