from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FloatField, DateField, BooleanField, SelectMultipleField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, URL, Optional
from app.models.models import User, Tags

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired('Please enter your username')])
    password = PasswordField('Password', validators=[DataRequired('Please enter your password')])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired('Please enter your username'), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired('Please enter your email'), Email('Invalid email format')])
    password = PasswordField('Password', validators=[DataRequired('Please enter your password'), Length(min=6)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired('Please confirm your password'), EqualTo('password', 'Passwords must match')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('This username is already taken')
            
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email is already registered')

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired('Please enter your username'), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired('Please enter your email'), Email('Invalid email format')])
    submit = SubmitField('Save Changes')
    
    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('This username is already taken')

class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired('Please enter your comment'), Length(max=255)])
    submit = SubmitField('Submit Comment')

class RateForm(FlaskForm):
    mark = FloatField('Rating', validators=[DataRequired('Please enter your rating')])
    submit = SubmitField('Submit Rating')

class MovieUploadForm(FlaskForm):
    csv_file = FileField('CSV File', validators=[
        FileRequired('Please select a file'),
        FileAllowed(['csv'], 'Only CSV files allowed')
    ])
    submit = SubmitField('Upload')

class MovieForm(FlaskForm):
    name = StringField('Movie Title', validators=[DataRequired('Please enter the movie title')])
    director = StringField('Director', validators=[DataRequired('Please enter the director')])
    country = StringField('Country', validators=[DataRequired('Please enter the country')])
    years = DateField('Release Date', validators=[DataRequired('Please enter the release date')])
    leader = StringField('Main Cast', validators=[DataRequired('Please enter the main cast')])
    d_rate_nums = StringField('Douban Rating Count', validators=[DataRequired('Please enter the Douban rating count')])
    d_rate = StringField('Douban Rating', validators=[DataRequired('Please enter the Douban rating')])
    intro = TextAreaField('Introduction', validators=[DataRequired('Please enter an introduction')])
    origin_image_link = StringField('Douban Image Link', validators=[Optional(), URL('Please enter a valid URL')])
    image_link = FileField('Cover Image', validators=[FileRequired('Please select an image'), FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Only image files allowed')])
    imdb_link = StringField('IMDB Link', validators=[Optional(), URL('Please enter a valid URL')])
    douban_link = StringField('Douban Link', validators=[DataRequired('Please enter the Douban link'), URL('Please enter a valid URL')])
    douban_id = StringField('Douban ID', validators=[Optional()])
    tags = SelectMultipleField('Tags', coerce=int)
    submit = SubmitField('Add Movie')
    
    def __init__(self, *args, **kwargs):
        super(MovieForm, self).__init__(*args, **kwargs)
        # 确保标签选择不重复
        unique_tags = {tag.id: tag for tag in Tags.query.all()}
        self.tags.choices = [(tag_id, tag.name) for tag_id, tag in unique_tags.items()]
        
    def validate_tags(self, field):
        """验证标签选择，确保没有重复提交"""
        # 去重处理
        field.data = list(set(field.data))

class SharedRecommendationForm(FlaskForm):
    title = StringField('Share Title', validators=[DataRequired('Please enter a title'), Length(max=255)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    movies = SelectMultipleField('Movies', coerce=int, validators=[DataRequired('Please select at least one movie')])
    shared_with = SelectMultipleField('Share With', coerce=int)
    is_public = BooleanField('Public Share')
    submit = SubmitField('Create Share')
    
    def __init__(self, current_user_id, *args, **kwargs):
        super(SharedRecommendationForm, self).__init__(*args, **kwargs)
        from app.models.models import Movie, User
        self.movies.choices = [(movie.id, movie.name) for movie in Movie.query.all()]
        self.shared_with.choices = [(user.id, user.username) for user in User.query.filter(User.id != current_user_id).all()]

class TagPreferForm(FlaskForm):
    tags = SelectMultipleField('Select Tags', coerce=int, validators=[DataRequired('Please select at least one tag')])
    submit = SubmitField('Save Preferences')
    
    def __init__(self, *args, **kwargs):
        super(TagPreferForm, self).__init__(*args, **kwargs)
        self.tags.choices = [(tag.id, tag.name) for tag in Tags.query.all()] 
