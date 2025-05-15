from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, abort
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, TextAreaField, IntegerField, FloatField, BooleanField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional
from sqlalchemy import func
from create_app import db
from models.models import User, Movie, Tags, Rate, Comment, LikeComment, UserTagPrefer, SharedRecommendation, MovieUpload
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import uuid
import os

from utils.file_handlers import save_file

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin auth middleware
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session or not session['admin_logged_in']:
            # Also check if the current user is admin
            if session.get('login_in') and session.get('user_id'):
                user = User.query.get(session.get('user_id'))
                if user and user.username == 'admin':
                    # If admin user is logged in, automatically set admin privileges
                    session['admin_logged_in'] = True
                    return f(*args, **kwargs)
            
            flash('Admin access required', 'danger')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Admin login form
class AdminLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

# Admin routes
@admin_bp.route('/')
@admin_required
def index():
    # Dashboard statistics
    user_count = User.query.count()
    movie_count = Movie.query.count()
    comment_count = Comment.query.count()
    rate_count = Rate.query.count()
    
    # Recent activities
    recent_users = User.query.order_by(User.created_time.desc()).limit(5).all()
    recent_comments = Comment.query.order_by(Comment.create_time.desc()).limit(5).all()
    recent_rates = Rate.query.order_by(Rate.create_time.desc()).limit(5).all()
    
    return render_template('admin/index.html', 
                           user_count=user_count,
                           movie_count=movie_count,
                           comment_count=comment_count,
                           rate_count=rate_count,
                           recent_users=recent_users,
                           recent_comments=recent_comments,
                           recent_rates=recent_rates)

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = AdminLoginForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        # Check if this is the admin user
        if username == 'admin':
            user = User.query.filter_by(username='admin').first()
            if user and user.password == password:
                session['admin_logged_in'] = True
                session['login_in'] = True  # Also set regular user login status
                session['user_id'] = user.id
                session['name'] = username
                flash('Logged in successfully as admin', 'success')
                return redirect(url_for('admin.index'))
            else:
                flash('Invalid admin password', 'danger')
        else:
            flash('Admin account does not exist', 'danger')
    
    return render_template('admin/login.html', form=form)

@admin_bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('admin.login'))

# User Management
@admin_bp.route('/users')
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users/index.html', users=users)

@admin_bp.route('/users/<int:id>')
@admin_required
def user_detail(id):
    user = User.query.get_or_404(id)
    return render_template('admin/users/detail.html', user=user, Rate=Rate, Comment=Comment)

@admin_bp.route('/users/<int:id>/delete', methods=['POST'])
@admin_required
def user_delete(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully', 'success')
    return redirect(url_for('admin.users'))

# Movie Management
@admin_bp.route('/movies')
@admin_required
def movies():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 每页显示10条记录
    
    pagination = Movie.query.order_by(Movie.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    movies = pagination.items
    
    return render_template('admin/movies/index.html', movies=movies, pagination=pagination)

@admin_bp.route('/movies/<int:id>')
@admin_required
def movie_detail(id):
    movie = Movie.query.get_or_404(id)
    return render_template('admin/movies/detail.html', movie=movie, Comment=Comment, Rate=Rate)

@admin_bp.route('/movies/create', methods=['GET', 'POST'])
@admin_required
def movie_create():
    if request.method == 'POST':
        try:
            name = request.form['name']
            director = request.form['director']
            country = request.form['country']
            years = datetime.datetime.strptime(request.form['years'], '%Y-%m-%d').date()
            leader = request.form['leader']
            d_rate_nums = int(request.form['d_rate_nums'])
            d_rate = request.form['d_rate']
            intro = request.form['intro']
            
            # 处理图片上传
            image_link = ''
            if 'image_file' in request.files and request.files['image_file'].filename:
                # 使用文件上传
                image_file = request.files['image_file']
                # 确保图片保存到media/movie_cover目录
                media_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'media', 'movie_cover')
                image_link = save_file(image_file, media_dir)
            elif request.form['image_link']:
                # 使用URL
                image_link = request.form['image_link']
                # 检查image_link是否是本地相对路径或绝对URL
                if image_link and not image_link.startswith(('http://', 'https://')):
                    # 如果是相对路径，确保不要重复添加MEDIA_URL前缀
                    if image_link.startswith('/media/'):
                        image_link = image_link[7:]  # 移除'/media/'前缀
            
            douban_link = request.form['douban_link']
            
            # Optional fields
            origin_image_link = request.form.get('origin_image_link', '')
            imdb_link = request.form.get('imdb_link', '')
            douban_id = request.form.get('douban_id', '')
            
            movie = Movie(
                name=name,
                director=director,
                country=country,
                years=years,
                leader=leader,
                d_rate_nums=d_rate_nums,
                d_rate=d_rate,
                intro=intro,
                image_link=image_link,
                douban_link=douban_link,
                origin_image_link=origin_image_link,
                imdb_link=imdb_link,
                douban_id=douban_id
            )
            
            # Add tags if provided
            tag_ids = request.form.getlist('tags')
            if tag_ids:
                tags = Tags.query.filter(Tags.id.in_(tag_ids)).all()
                movie.tags = tags
            
            db.session.add(movie)
            db.session.commit()
            flash('Movie created successfully', 'success')
            return redirect(url_for('admin.movies'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating movie: {str(e)}', 'danger')
    
    # Get all tags for selection
    tags = Tags.query.all()
    return render_template('admin/movies/create.html', tags=tags)

@admin_bp.route('/movies/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def movie_edit(id):
    movie = Movie.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            movie.name = request.form['name']
            movie.director = request.form['director']
            movie.country = request.form['country']
            movie.years = datetime.datetime.strptime(request.form['years'], '%Y-%m-%d').date()
            movie.leader = request.form['leader']
            movie.d_rate_nums = int(request.form['d_rate_nums'])
            movie.d_rate = request.form['d_rate']
            movie.intro = request.form['intro']
            
            # 处理图片上传
            if 'image_file' in request.files and request.files['image_file'].filename:
                # 使用文件上传
                image_file = request.files['image_file']
                # 确保图片保存到media/movie_cover目录
                media_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'media', 'movie_cover')
                image_link = save_file(image_file, media_dir)
                movie.image_link = image_link
            elif request.form['image_link'] and request.form['image_link'] != movie.image_link:
                # 使用URL，且URL已更改
                image_link = request.form['image_link']
                # 检查image_link是否是本地相对路径或绝对URL
                if image_link and not image_link.startswith(('http://', 'https://')):
                    # 如果是相对路径，确保不要重复添加MEDIA_URL前缀
                    if image_link.startswith('/media/'):
                        image_link = image_link[7:]  # 移除'/media/'前缀
                movie.image_link = image_link
            
            movie.douban_link = request.form['douban_link']
            
            # Optional fields
            movie.origin_image_link = request.form.get('origin_image_link', '')
            movie.imdb_link = request.form.get('imdb_link', '')
            movie.douban_id = request.form.get('douban_id', '')
            
            # Update tags
            tag_ids = request.form.getlist('tags')
            if tag_ids:
                tags = Tags.query.filter(Tags.id.in_(tag_ids)).all()
                movie.tags = tags
            else:
                movie.tags = []
            
            db.session.commit()
            flash('Movie updated successfully', 'success')
            return redirect(url_for('admin.movies'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating movie: {str(e)}', 'danger')
    
    # Get all tags for selection
    tags = Tags.query.all()
    return render_template('admin/movies/edit.html', movie=movie, tags=tags)

@admin_bp.route('/movies/<int:id>/delete', methods=['POST'])
@admin_required
def movie_delete(id):
    movie = Movie.query.get_or_404(id)
    db.session.delete(movie)
    db.session.commit()
    flash('Movie deleted successfully', 'success')
    return redirect(url_for('admin.movies'))

# Tags Management
@admin_bp.route('/tags')
@admin_required
def tags():
    tags = Tags.query.all()
    return render_template('admin/tags/index.html', tags=tags)

@admin_bp.route('/tags/create', methods=['GET', 'POST'])
@admin_required
def tag_create():
    if request.method == 'POST':
        try:
            name = request.form['name']
            tag = Tags(name=name)
            db.session.add(tag)
            db.session.commit()
            flash('Tag created successfully', 'success')
            return redirect(url_for('admin.tags'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating tag: {str(e)}', 'danger')
    
    return render_template('admin/tags/create.html')

@admin_bp.route('/tags/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def tag_edit(id):
    tag = Tags.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            tag.name = request.form['name']
            db.session.commit()
            flash('Tag updated successfully', 'success')
            return redirect(url_for('admin.tags'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating tag: {str(e)}', 'danger')
    
    return render_template('admin/tags/edit.html', tag=tag)

@admin_bp.route('/tags/<int:id>/delete', methods=['POST'])
@admin_required
def tag_delete(id):
    tag = Tags.query.get_or_404(id)
    db.session.delete(tag)
    db.session.commit()
    flash('Tag deleted successfully', 'success')
    return redirect(url_for('admin.tags'))

# Comments Management
@admin_bp.route('/comments')
@admin_required
def comments():
    comments = Comment.query.all()
    return render_template('admin/comments/index.html', comments=comments)

@admin_bp.route('/comments/<int:id>/delete', methods=['POST'])
@admin_required
def comment_delete(id):
    comment = Comment.query.get_or_404(id)
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted successfully', 'success')
    return redirect(url_for('admin.comments'))

# Rates Management
@admin_bp.route('/rates')
@admin_required
def rates():
    rates = Rate.query.all()
    return render_template('admin/rates/index.html', rates=rates)

@admin_bp.route('/rates/<int:id>/delete', methods=['POST'])
@admin_required
def rate_delete(id):
    rate = Rate.query.get_or_404(id)
    db.session.delete(rate)
    db.session.commit()
    flash('Rate deleted successfully', 'success')
    return redirect(url_for('admin.rates'))

# UserTagPrefer Management
@admin_bp.route('/user_tag_prefers')
@admin_required
def user_tag_prefers():
    prefers = UserTagPrefer.query.all()
    return render_template('admin/user_tag_prefers/index.html', prefers=prefers)

# SharedRecommendation Management
@admin_bp.route('/shared_recommendations')
@admin_required
def shared_recommendations():
    recommendations = SharedRecommendation.query.all()
    return render_template('admin/shared_recommendations/index.html', recommendations=recommendations)

# MovieUpload Management
@admin_bp.route('/movie_uploads')
@admin_required
def movie_uploads():
    uploads = MovieUpload.query.all()
    return render_template('admin/movie_uploads/index.html', uploads=uploads) 