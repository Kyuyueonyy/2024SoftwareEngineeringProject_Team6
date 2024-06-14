from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_wtf.file import FileField, FileAllowed
from app.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    user_id = StringField('User ID', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_user_id(self, user_id):
        user = User.query.filter_by(user_id=user_id.data).first()
        if user:
            raise ValidationError('That user ID is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    user_id = StringField('User ID', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class UploadForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = StringField('Content', validators=[DataRequired()])
    keyword = StringField('Keyword', validators=[DataRequired()])
    photo = FileField('Photo', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Upload')

class CommentForm(FlaskForm):
    content = StringField('Comment', validators=[DataRequired()])
    submit = SubmitField('Post Comment')

class ProfileForm(FlaskForm):
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

class SearchForm(FlaskForm):
    search = StringField('Search', validators=[DataRequired()])
    search_by = SelectField('Search By', choices=[('title', 'Title'), ('keyword', 'Keyword'), ('username', 'Username')])
    submit = SubmitField('Search')
