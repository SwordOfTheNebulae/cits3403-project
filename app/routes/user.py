from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, abort, current_app
from create_app import db
from sqlalchemy import func
from models.models import User, Movie, Rate, Comment, LikeComment, MovieUpload, SharedRecommendation, Tags
from utils.decorators import login_required
from utils.forms import EditProfileForm, CommentForm, RateForm, MovieUploadForm, MovieForm, MovieEditForm, SharedRecommendationForm
from utils.file_handlers import allowed_file, save_file, process_csv_file
import os
import uuid
from datetime import datetime
import csv
from werkzeug.utils import secure_filename
from io import StringIO

user_bp = Blueprint('user', __name__)


@user_bp.route('/personal', methods=['GET', 'POST'])
@login_required
def personal():
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)

    form = EditProfileForm(user.username)

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        db.session.commit()

        session['name'] = user.username
        flash('Profile updated successfully', 'success')
        return redirect(url_for('user.personal'))

    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email

    return render_template('user/personal.html', user=user, form=form, title='Personal Information')


@user_bp.route('/comment/<int:movie_id>', methods=['POST'])
@login_required
def make_comment(movie_id):
    content = request.form.get('content')
    if not content or len(content) > 255:
        flash('Comment cannot be empty and must be less than 255 characters', 'danger')
        return redirect(url_for('movie.movie_detail', movie_id=movie_id))

    user_id = session.get('user_id')

    comment = Comment(user_id=user_id, movie_id=movie_id, content=content)
    db.session.add(comment)
    db.session.commit()

    flash('Comment added successfully', 'success')
    return redirect(url_for('movie.movie_detail', movie_id=movie_id))


@user_bp.route('/my_comments')
@login_required
def my_comments():
    user_id = session.get('user_id')
    item = Comment.query.filter_by(user_id=user_id).order_by(Comment.create_time.desc()).all()
    return render_template('user/my_comment.html', item=item)


@user_bp.route('/like_comment/<int:comment_id>/<int:movie_id>')
@login_required
def like_comment(comment_id, movie_id):
    user_id = session.get('user_id')

    # 检查是否已点赞
    existing_like = LikeComment.query.filter_by(user_id=user_id, comment_id=comment_id).first()

    if not existing_like:
        like = LikeComment(user_id=user_id, comment_id=comment_id)
        db.session.add(like)
        db.session.commit()

    return redirect(url_for('movie.movie_detail', movie_id=movie_id))


@user_bp.route('/unlike_comment/<int:comment_id>/<int:movie_id>')
@login_required
def unlike_comment(comment_id, movie_id):
    user_id = session.get('user_id')

    existing_like = LikeComment.query.filter_by(user_id=user_id, comment_id=comment_id).first()

    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()

    return redirect(url_for('movie.movie_detail', movie_id=movie_id))


@user_bp.route('/delete_comment/<int:comment_id>')
@login_required
def delete_comment(comment_id):
    user_id = session.get('user_id')
    comment = Comment.query.get_or_404(comment_id)

    if comment.user_id != user_id:
        abort(403)
    
    # 先删除与评论相关的所有点赞记录
    LikeComment.query.filter_by(comment_id=comment_id).delete()
    
    # 然后删除评论
    db.session.delete(comment)
    db.session.commit()

    flash('Comment deleted', 'success')
    return redirect(url_for('user.my_comments'))


@user_bp.route('/rate/<int:movie_id>', methods=['POST'])
@login_required
def rate_movie(movie_id):
    mark = request.form.get('mark')
    if not mark:
        flash('Please enter a rating', 'danger')
        return redirect(url_for('movie.movie_detail', movie_id=movie_id))

    try:
        mark = float(mark)
        if mark < 0 or mark > 10:
            raise ValueError
    except ValueError:
        flash('Rating must be a number between 0-10', 'danger')
        return redirect(url_for('movie.movie_detail', movie_id=movie_id))

    user_id = session.get('user_id')

    # 检查是否已评分
    existing_rate = Rate.query.filter_by(user_id=user_id, movie_id=movie_id).first()

    if existing_rate:
        existing_rate.mark = mark
    else:
        rate = Rate(user_id=user_id, movie_id=movie_id, mark=mark)
        db.session.add(rate)

    db.session.commit()

    flash('Rating added successfully', 'success')
    return redirect(url_for('movie.movie_detail', movie_id=movie_id))


@user_bp.route('/my_rate')
@login_required
def my_rate():
    user_id = session.get('user_id')
    item = Rate.query.filter_by(user_id=user_id).order_by(Rate.create_time.desc()).all()
    return render_template('user/my_rate.html', item=item)


@user_bp.route('/delete_rate/<int:rate_id>')
@login_required
def delete_rate(rate_id):
    user_id = session.get('user_id')
    rate = Rate.query.get_or_404(rate_id)

    if rate.user_id != user_id:
        abort(403)

    db.session.delete(rate)
    db.session.commit()

    flash('Rating deleted', 'success')
    return redirect(url_for('user.my_rate'))


@user_bp.route('/collect/<int:movie_id>')
@login_required
def collect(movie_id):
    user_id = session.get('user_id')
    movie = Movie.query.get_or_404(movie_id)
    user = User.query.get_or_404(user_id)

    # 检查是否已收藏
    if user in movie.collect:
        flash('You have already collected this movie', 'warning')
    else:
        movie.collect.append(user)
        db.session.commit()
        flash('Movie collected successfully', 'success')

    return redirect(url_for('movie.movie_detail', movie_id=movie_id))


@user_bp.route('/decollect/<int:movie_id>')
@login_required
def decollect(movie_id):
    user_id = session.get('user_id')
    movie = Movie.query.get_or_404(movie_id)
    user = User.query.get_or_404(user_id)

    if user in movie.collect:
        movie.collect.remove(user)
        db.session.commit()
        flash('Collection removed', 'success')

    return redirect(url_for('movie.movie_detail', movie_id=movie_id))


@user_bp.route('/mycollect')
@login_required
def mycollect():
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)
    item = user.collected_movies

    return render_template('user/mycollect.html', item=item)

@user_bp.route('/upload_movie_csv', methods=['GET', 'POST'])
@login_required
def upload_movie_csv():
    form = MovieUploadForm()

    if form.validate_on_submit():
        user_id = session.get('user_id')
        csv_file = form.csv_file.data

        if csv_file and allowed_file(csv_file.filename, {'csv'}):
            try:
                # 保存上传文件 - 修正保存路径避免重复的子目录
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'movie_uploads')
                filename = save_file(csv_file, upload_dir)
                
                # 创建上传记录
                upload = MovieUpload(
                    user_id=user_id,
                    csv_file=filename,
                    status='pending',
                    uploaded_at=datetime.utcnow()
                )
                db.session.add(upload)
                db.session.commit()
                
                # 处理CSV文件 - 使用正确的完整文件路径
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                
                # 创建一个函数在应用上下文中运行process_csv_file
                def process_with_app_context(app, file_path, upload_id):
                    with app.app_context():
                        process_csv_file(file_path, upload_id)
                
                # 使用单独的线程处理CSV文件，并传入应用上下文
                import threading
                thread = threading.Thread(
                    target=process_with_app_context,
                    args=(current_app._get_current_object(), file_path, upload.id)
                )
                thread.daemon = True
                thread.start()
                
                flash('File uploaded successfully. Processing in background...', 'success')
                return redirect(url_for('user.movie_upload_list'))
                
            except Exception as e:
                flash(f'Upload failed: {str(e)}', 'danger')
                return redirect(url_for('user.upload_movie_csv'))
        else:
            flash('Please upload a CSV file', 'danger')

    # 提供CSV示例
    csv_example = [
        "name,director,country,years,leader,d_rate_nums,d_rate,intro,tags,douban_link,douban_id",
        "Example Movie Name,Director Name,Country,2023-01-01,Lead Actor Name,1000,8.5,Movie Introduction,Comedy|Action|Adventure,https://movie.douban.com/xxx,12345678"
    ]
    
    return render_template('user/upload_movie.html', 
                           form=form, 
                           csv_example='\n'.join(csv_example))


@user_bp.route('/movie_upload_list')
@login_required
def movie_upload_list():
    user_id = session.get('user_id')
    uploads = MovieUpload.query.filter_by(user_id=user_id).order_by(MovieUpload.uploaded_at.desc()).all()

    return render_template('user/movie_upload_list.html', uploads=uploads)


@user_bp.route('/upload_status/<int:upload_id>')
@login_required
def upload_status(upload_id):
    user_id = session.get('user_id')
    upload = MovieUpload.query.get_or_404(upload_id)

    if upload.user_id != user_id:
        abort(403)

    # 从notes字段获取导入的电影ID
    movies = []
    if upload.notes and upload.status == 'completed':
        try:
            import json
            data = json.loads(upload.notes)
            if 'imported_movie_ids' in data:
                # 获取导入的电影
                movie_ids = data['imported_movie_ids']
                movies = Movie.query.filter(Movie.id.in_(movie_ids)).all()
        except (json.JSONDecodeError, ValueError) as e:
            # 如果无法解析JSON，记录错误
            print(f"Error parsing JSON: {str(e)}")
            
    # 如果是API请求，返回JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'status': upload.status,
            'processed_count': upload.processed_count,
        })

    return render_template('user/upload_movie_detail.html', upload=upload, movies=movies)


@user_bp.route('/add_movie_manual', methods=['GET', 'POST'])
@login_required
def add_movie_manual():
    form = MovieForm()

    if form.validate_on_submit():
        try:
            # 保存图片
            image_file = form.image_link.data
            # 确保图片保存到media/movie_cover目录
            media_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'media', 'movie_cover')
            image_filename = save_file(image_file, media_dir)

            # 创建电影
            movie = Movie(
                name=form.name.data,
                director=form.director.data,
                country=form.country.data,
                years=form.years.data,
                leader=form.leader.data,
                d_rate_nums=form.d_rate_nums.data,
                d_rate=form.d_rate.data,
                intro=form.intro.data,
                origin_image_link=form.origin_image_link.data,
                image_link=image_filename,
                imdb_link=form.imdb_link.data,
                douban_link=form.douban_link.data,
                douban_id=form.douban_id.data
            )

            # 添加标签 - 使用set去重处理
            tag_ids = set(form.tags.data)  # 使用set去除可能的重复tag_id
            # 一次性查询所有标签
            tags = Tags.query.filter(Tags.id.in_(tag_ids)).all()
            # 清空标签列表并重新添加
            movie.tags = []
            for tag in tags:
                movie.tags.append(tag)

            db.session.add(movie)
            db.session.commit()

            flash(f'Movie "{movie.name}" added successfully', 'success')
            
            # 重定向到相同页面但使用GET请求，这样会清空表单
            return redirect(url_for('user.add_movie_manual'))
        except Exception as e:
            db.session.rollback()
            
            # 详细记录异常信息
            import traceback
            error_details = traceback.format_exc()
            print(f"Error adding movie: {str(e)}\n{error_details}")
            
            # 分析具体错误类型，给用户更友好的提示
            error_str = str(e)
            if 'UNIQUE constraint failed: movie_tags.movie_id, movie_tags.tag_id' in error_str:
                flash('添加电影失败：标签重复提交。请确保每个标签只选择一次。', 'danger')
            elif 'IntegrityError' in error_str:
                flash('添加电影失败：数据完整性错误。请检查必填字段是否都已填写。', 'danger')
            else:
                flash(f'添加电影失败: {error_str}', 'danger')

    # 检查表单验证错误
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error in {field}: {error}', 'danger')
                print(f"Form validation error in {field}: {error}")

    return render_template('user/add_movie.html', form=form)


@user_bp.route('/get_csv_template')
def get_csv_template():
    # 创建CSV模板
    csv_data = StringIO()
    writer = csv.writer(csv_data)

    # 写入表头
    headers = ['name', 'director', 'country', 'years', 'leader', 'd_rate_nums', 'd_rate', 'intro', 'origin_image_link',
               'douban_link', 'douban_id', 'imdb_link', 'tags']
    writer.writerow(headers)

    # 写入示例数据
    example = ['Movie Title', 'Director Name', 'Country', '2023-01-01', 'Lead Actor', '10000', '9.0', 'Movie Introduction',
               'http://example.com/image.jpg', 'http://douban.com/movie/123', '123456', 'http://imdb.com/title/123',
               'Comedy|Action|Adventure']
    writer.writerow(example)

    # 设置响应头
    from flask import Response
    response = Response(
        csv_data.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename="movie_template.csv"'}
    )

    return response


def get_recommendation_movies(user_id):
    """
    获取用户的收藏、评分及推荐电影数据
    """
    # 获取用户的收藏和评分过的电影
    user = User.query.get(user_id)
    
    # 用户收藏的电影
    collected_movies = user.collected_movies if hasattr(user, 'collected_movies') else []
    
    # 用户评分的电影
    rated_movies = Movie.query.join(Rate).filter(Rate.user_id == user_id).all()
    
    # 合并用户的收藏和评分电影并去重
    user_movies = list({movie.id: movie for movie in (collected_movies + rated_movies)}.values())
    
    # 基于用户的推荐
    user_rec_movies = []
    # 尝试导入并使用推荐模块
    try:
        # 如果用户没有评分，则返回随机电影或基于标签的推荐
        if not rated_movies:
            # 获取用户标签偏好
            tag_prefers = UserTagPrefer.query.filter_by(user_id=user_id).order_by(UserTagPrefer.score.desc()).all()
            if tag_prefers:
                # 获取用户喜欢的标签对应的电影
                tag_ids = [prefer.tag_id for prefer in tag_prefers]
                tag_movies = Movie.query.filter(Movie.tags.any(Tags.id.in_(tag_ids))).limit(15).all()
                user_rec_movies = tag_movies
            else:
                # 如果用户没有标签偏好，返回随机电影
                user_rec_movies = Movie.query.order_by(func.random()).limit(15).all()
        else:
            # 如果推荐函数可用，使用推荐函数
            try:
                from recommend_movies import recommend_by_user_id
                # 调用外部推荐函数
                result = recommend_by_user_id(user_id)
                if result and isinstance(result, list):
                    user_rec_movies = result
            except (ImportError, AttributeError) as e:
                print(f"推荐函数不可用: {str(e)}")
                # 返回最近添加的电影
                user_rec_movies = Movie.query.order_by(Movie.id.desc()).limit(15).all()
    except Exception as e:
        print(f"获取用户推荐出错: {str(e)}")
        # 出错时返回最新电影
        user_rec_movies = Movie.query.order_by(Movie.id.desc()).limit(15).all()
    
    # 基于物品的推荐
    item_rec_movies = []
    try:
        # 如果用户有评分记录，使用基于物品的推荐
        if rated_movies:
            try:
                from recommend_movies import recommend_by_item_id
                # 调用外部推荐函数
                result = recommend_by_item_id(user_id)
                if result and isinstance(result, list):
                    item_rec_movies = result
            except (ImportError, AttributeError) as e:
                print(f"物品推荐函数不可用: {str(e)}")
                # 返回热门电影
                item_rec_movies = Movie.query.order_by(Movie.num.desc()).limit(15).all()
        else:
            # 用户没有评分记录，返回热门电影
            item_rec_movies = Movie.query.order_by(Movie.num.desc()).limit(15).all()
    except Exception as e:
        print(f"获取物品推荐出错: {str(e)}")
        # 出错时返回热门电影
        item_rec_movies = Movie.query.order_by(Movie.num.desc()).limit(15).all()
    
    print(f"User movies: {len(user_movies)}, User rec: {len(user_rec_movies)}, Item rec: {len(item_rec_movies)}")
    
    return user_movies, user_rec_movies, item_rec_movies

@user_bp.route('/create_share', methods=['GET', 'POST'])
@login_required
def create_shared_recommendation():
    user_id = session.get('user_id')
    form = SharedRecommendationForm(user_id)

    if form.validate_on_submit():
        # 生成唯一分享密钥
        share_key = str(uuid.uuid4())

        # 创建分享
        share = SharedRecommendation(
            user_id=user_id,
            share_key=share_key,
            title=form.title.data,
            description=form.description.data,
            is_public=form.is_public.data
        )

        # 添加电影 - 去重处理
        movie_ids = set(request.form.getlist('movies'))  # 使用set去除重复的电影ID
        for movie_id in movie_ids:
            movie = Movie.query.get(movie_id)
            if movie:
                share.movies.append(movie)

        # 添加分享对象
        if not form.is_public.data and form.shared_with.data:
            for shared_user_id in form.shared_with.data:
                user = User.query.get(shared_user_id)
                if user:
                    share.shared_with.append(user)

        db.session.add(share)
        db.session.commit()

        flash('Share created successfully', 'success')
        return redirect(url_for('user.view_my_shares'))

    # 获取推荐电影数据
    user_movies, user_rec_movies, item_rec_movies = get_recommendation_movies(user_id)

    return render_template('user/create_share.html', 
                          form=form,
                          user_movies=user_movies,
                          user_rec_movies=user_rec_movies,
                          item_rec_movies=item_rec_movies)


@user_bp.route('/my_shares')
@login_required
def view_my_shares():
    user_id = session.get('user_id')
    shares = SharedRecommendation.query.filter_by(user_id=user_id).order_by(
        SharedRecommendation.created_at.desc()).all()

    return render_template('user/my_shares.html', shares=shares)


@user_bp.route('/edit_share/<int:share_id>', methods=['GET', 'POST'])
@login_required
def edit_share(share_id):
    user_id = session.get('user_id')
    share = SharedRecommendation.query.get_or_404(share_id)

    if share.user_id != user_id:
        abort(403)

    form = SharedRecommendationForm(user_id)

    if form.validate_on_submit():
        # 更新基本信息
        share.title = form.title.data
        share.description = form.description.data
        share.is_public = form.is_public.data

        # 更新电影 - 去重处理
        share.movies.clear()
        movie_ids = set(request.form.getlist('movies'))  # 使用set去除重复的电影ID
        for movie_id in movie_ids:
            movie = Movie.query.get(movie_id)
            if movie:
                share.movies.append(movie)

        # 更新分享对象
        share.shared_with.clear()
        if not form.is_public.data and form.shared_with.data:
            for shared_user_id in form.shared_with.data:
                user = User.query.get(shared_user_id)
                if user:
                    share.shared_with.append(user)

        db.session.commit()

        flash('Share updated successfully', 'success')
        return redirect(url_for('user.view_my_shares'))

    elif request.method == 'GET':
        form.title.data = share.title
        form.description.data = share.description
        form.is_public.data = share.is_public
        form.movies.data = [movie.id for movie in share.movies]
        form.shared_with.data = [user.id for user in share.shared_with]

    # 获取推荐电影数据
    user_movies, user_rec_movies, item_rec_movies = get_recommendation_movies(user_id)

    # 获取已选择的电影ID
    selected_movie_ids = [str(movie.id) for movie in share.movies]
    
    return render_template('user/edit_share.html', 
                          form=form, 
                          share=share,
                          user_movies=user_movies,
                          user_rec_movies=user_rec_movies,
                          item_rec_movies=item_rec_movies,
                          selected_movie_ids=selected_movie_ids)


@user_bp.route('/delete_share/<int:share_id>')
@login_required
def delete_share(share_id):
    user_id = session.get('user_id')
    share = SharedRecommendation.query.get_or_404(share_id)

    if share.user_id != user_id:
        abort(403)

    db.session.delete(share)
    db.session.commit()

    flash('Share deleted', 'success')
    return redirect(url_for('user.view_my_shares'))


@user_bp.route('/view_shared/<share_key>')
def view_shared(share_key):
    share = SharedRecommendation.query.filter_by(share_key=share_key).first_or_404()

    # 检查访问权限
    user_id = session.get('user_id')

    if not share.is_public and (not user_id or user_id not in [user.id for user in share.shared_with]):
        if user_id != share.user_id:
            abort(403)

    # 获取创建者信息
    creator = User.query.get(share.user_id)
    if not creator:
        abort(404)

    # 获取分享电影
    movies = share.movies

    return render_template('user/view_shared.html', share=share, movies=movies, creator=creator)


@user_bp.route('/shared_with_me')
@login_required
def shared_with_me():
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)

    # 获取分享给当前用户的推荐
    shared_with_user = user.shared_to_me

    # 获取公开分享的推荐
    public_shares = SharedRecommendation.query.filter_by(is_public=True).all()

    # 合并并去重
    shares = list(set(shared_with_user + public_shares))

    return render_template('user/shared_with_me.html', shares=shares)

@user_bp.route('/edit_imported_movie/<int:movie_id>/<int:upload_id>', methods=['GET', 'POST'])
@login_required
def edit_imported_movie(movie_id, upload_id):
    user_id = session.get('user_id')
    movie = Movie.query.get_or_404(movie_id)
    upload = MovieUpload.query.get_or_404(upload_id)
    
    # Verify user permission
    if upload.user_id != user_id:
        abort(403)
    
    form = MovieEditForm(obj=movie)
    
    if form.validate_on_submit():
        try:
            # Handle image upload
            if form.image_link.data and hasattr(form.image_link.data, 'filename') and form.image_link.data.filename:
                # Save new image
                media_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'media', 'movie_cover')
                image_filename = save_file(form.image_link.data, media_dir)
                movie.image_link = image_filename
            
            # Update movie data
            movie.name = form.name.data
            movie.director = form.director.data
            movie.country = form.country.data
            movie.years = form.years.data
            movie.leader = form.leader.data
            movie.d_rate_nums = form.d_rate_nums.data
            movie.d_rate = form.d_rate.data
            movie.intro = form.intro.data
            movie.origin_image_link = form.origin_image_link.data
            movie.imdb_link = form.imdb_link.data
            movie.douban_link = form.douban_link.data
            movie.douban_id = form.douban_id.data
            
            # Update tags
            tag_ids = set(form.tags.data)
            tags = Tags.query.filter(Tags.id.in_(tag_ids)).all()
            movie.tags = []
            for tag in tags:
                movie.tags.append(tag)
            
            db.session.commit()
            flash(f'Movie "{movie.name}" has been updated successfully', 'success')
            return redirect(url_for('user.upload_status', upload_id=upload_id))
            
        except Exception as e:
            db.session.rollback()
            import traceback
            error_details = traceback.format_exc()
            print(f"Error updating movie: {str(e)}\n{error_details}")
            flash(f'Failed to update movie: {str(e)}', 'danger')
    
    # For GET requests, pre-populate the form
    elif request.method == 'GET':
        # Pre-set tags
        form.tags.data = [tag.id for tag in movie.tags]
    
    # Handle form validation errors
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error in field {field}: {error}', 'danger')
    
    return render_template('user/edit_movie.html', form=form, movie=movie, upload_id=upload_id)

@user_bp.route('/delete_imported_movie/<int:movie_id>/<int:upload_id>')
@login_required
def delete_imported_movie(movie_id, upload_id):
    user_id = session.get('user_id')
    movie = Movie.query.get_or_404(movie_id)
    upload = MovieUpload.query.get_or_404(upload_id)
    
    # Verify user permission
    if upload.user_id != user_id:
        abort(403)
    
    try:
        # Simple direct deletion of the movie
        db.session.delete(movie)
        db.session.commit()
        
        flash(f'Movie "{movie.name}" has been deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting movie: {str(e)}")
        flash(f'Failed to delete movie: {str(e)}', 'danger')
    
    return redirect(url_for('user.upload_status', upload_id=upload_id))
