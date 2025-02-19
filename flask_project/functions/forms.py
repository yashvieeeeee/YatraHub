from flask_wtf import FlaskForm
from wtforms import StringField, DateField, IntegerField, SubmitField, HiddenField, SelectMultipleField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, NumberRange, Optional, EqualTo

class DestinationForm(FlaskForm):
    destination = StringField('Destination', validators=[DataRequired()])
    latitude = HiddenField('Latitude')
    longitude = HiddenField('Longitude')
    display_name = HiddenField('Display Name')
    submit = SubmitField('Next')

class DatesForm(FlaskForm):
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    num_travelers = IntegerField('Number of Travelers', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Next')

class AccommodationForm(FlaskForm):
    accommodation = StringField('Accommodation', validators=[DataRequired()])
    accommodation_details = TextAreaField('Accommodation Details', validators=[Optional()]) #Optional validator
    submit = SubmitField('Next')

class TransportationForm(FlaskForm):
    transportation_method = SelectMultipleField('Transportation Method', choices=[
        ('flight', 'Flight'),
        ('train', 'Train'),
        ('car_rental', 'Car Rental'),
        ('local_transport', 'Local Transport')
    ], validators=[DataRequired()])
    reason_for_visiting = TextAreaField('Reason for Visiting', validators=[Optional()])  # New field
    submit = SubmitField('Next')

class PlacesOfInterestForm(FlaskForm):
    places = SelectMultipleField('Places of Interest', choices=[], validators=[Optional()])
    submit = SubmitField('Next')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField(
        'Confirm Password', 
        validators=[DataRequired(), EqualTo('password', message='Passwords must match')]
    )
    submit = SubmitField('Sign Up')