from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    travelers = db.Column(db.Integer, nullable=False)
    accommodation = db.Column(db.String(100), nullable=False)
    transportation = db.Column(db.String(100), nullable=False)
    reason_for_visiting = db.Column(db.String(255), nullable=True)
    places_of_interest = db.Column(db.String(255), nullable=True)
    all_places = db.Column(db.Text, nullable=True)  # Add this field to store all places of interest
    gemini_info = db.Column(db.Text, nullable=True)
    estimated_cost = db.Column(db.Float, nullable=False)
    weather_info = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Trip(destination='{self.destination}', start_date='{self.start_date}', end_date='{self.end_date}')>"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    trips = db.relationship('Trip', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User(username='{self.username}')>"