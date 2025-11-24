from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField, SelectField, TextAreaField, BooleanField, FileField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

class RegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(), 
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', 
                                    validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ProfileForm(FlaskForm):  # NEW: Profile editing form
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    occupation = StringField('Occupation/Role', validators=[Optional(), Length(max=100)])
    profile_picture = FileField('Profile Picture')  # File upload field
    submit = SubmitField('Update Profile')

class PortfolioItemForm(FlaskForm):
    title = StringField('Project Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    youtube_id = StringField('YouTube Video ID', validators=[Optional(), Length(max=20)])
    category = SelectField('Category', choices=[
        ('creative', 'Creative & Content'),
        ('social', 'Social Growth'),
        ('marketing', 'Performance Marketing'),
        ('development', 'Web Development'),
        ('ai', 'AI Solutions')
    ], validators=[DataRequired()])
    tags = StringField('Tags (comma separated)', validators=[Optional()])
    is_coming_soon = BooleanField('Mark as Coming Soon')
    submit = SubmitField('Save Project')