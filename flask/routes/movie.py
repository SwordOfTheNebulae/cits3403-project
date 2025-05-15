from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, abort
from app.create_app import db
from sqlalchemy import func, or_, desc, text
from models.models import Movie, Tags, Rate, Comment, LikeComment, User
from utils.decorators import login_required
from utils.forms import CommentForm, RateForm
from utils.recommend import recommend_by_user_id, recommend_by_item_id, update_item_movie_sim_matrix
from flask_paginate import Pagination, get_page_parameter

movie_bp = Blueprint('movie', __name__)


def get_paginated_movies(movies, page, per_page=12):
    """获取分页后的电影"""
    offset = (page - 1) * per_page
    return movies.limit(per_page).offset(offset).all()


@movie_bp.route('/')
def index():
    # 获取排序参数
    order = request.args.get('order') or session.get('order')
    session['order'] = order
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 8

    # 根据排序参数获取电影列表
    if order == 'collect':
        # 按收藏数排序
        collectors = func.count(Movie.collect).label('collectors')
        movies_query = db.session.query(Movie, collectors) \
            .outerjoin(Movie.collect) \
            .group_by(Movie.id) \
            .order_by(desc(collectors))
        title = 'Sort by Collections'
    elif order == 'rate':
        # 按平均评分排序
        avg_mark = func.avg(Rate.mark).label('avg_mark')
        movies_query = db.session.query(Movie, avg_mark) \
            .outerjoin(Rate) \
            .group_by(Movie.id) \
            .order_by(desc(avg_mark))
        title = 'Sort by Ratings'
    elif order == 'years':
        # 按年份排序
        movies_query = Movie.query.order_by(Movie.years.desc())
        title = 'Sort by Year'
    else:
        # 默认按浏览量排序
        movies_query = Movie.query.order_by(Movie.num.desc())
        title = 'Popular Movies'

    # 分页处理
    total = movies_query.count()
    
    if order in ['collect', 'rate']:
        # 手动分页
        results = movies_query.limit(per_page).offset((page-1)*per_page).all()
        movies = [movie[0] for movie in results]
    else:
        # 使用paginate
        movies = movies_query.paginate(page=page, per_page=per_page, error_out=False).items

    # 获取最新电影
    new_list = Movie.query.order_by(Movie.years.desc()).limit(8).all()

    # 如果用户已登录，获取基于用户的推荐列表
    user_recommend_list = []
    if session.get('login_in'):
        user_id = session.get('user_id')
        user_recommend_list = recommend_by_user_id(user_id, 8)

    pagination = Pagination(page=page, total=total, per_page=per_page,
                            css_framework='bootstrap4')

    return render_template('user/items.html',
                           movies=movies,
                           new_list=new_list,
                           title=title,
                           user_recommend_list=user_recommend_list,
                           pagination=pagination)


@movie_bp.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    # 获取电影详情
    movie = Movie.query.get_or_404(movie_id)

    # 增加浏览量
    movie.num += 1
    db.session.commit()

    # 获取评论
    comments = Comment.query.filter_by(movie_id=movie_id).order_by(Comment.create_time.desc()).all()

    # 获取电影平均评分
    movie_rate = db.session.query(func.avg(Rate.mark)).filter(Rate.movie_id == movie_id).scalar()
    if not movie_rate:
        movie_rate = 0

    # 检查用户是否已评分和收藏
    user_id = session.get('user_id')
    user_rate = None
    is_collect = False
    user = None

    if user_id:
        user = User.query.get(user_id)
        user_rate = Rate.query.filter_by(movie_id=movie_id, user_id=user_id).first()
        is_collect = user in movie.collect

    return render_template('user/movie.html',
                           movie=movie,
                           comments=comments,
                           movie_rate=movie_rate,
                           user_rate=user_rate,
                           is_collect=is_collect,
                           user=user)


@movie_bp.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        key = request.form.get('search')
        session['search'] = key
    else:
        key = session.get('search')

    if not key:
        return redirect(url_for('movie.index'))

    # 查询匹配关键词的电影
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 12

    query = Movie.query.filter(
        or_(
            Movie.name.contains(key),
            Movie.intro.contains(key),
            Movie.director.contains(key)
        )
    )

    total = query.count()
    movies = query.paginate(page=page, per_page=per_page, error_out=False).items

    pagination = Pagination(page=page, total=total, per_page=per_page,
                            css_framework='bootstrap4')

    return render_template('user/items.html',
                           movies=movies,
                           title='Search Results',
                           pagination=pagination)


@movie_bp.route('/tags')
def all_tags():
    tags = Tags.query.all()
    return render_template('user/all_tags.html', all_tags=tags)


@movie_bp.route('/tag/<int:tag_id>')
def tag_movies(tag_id):
    tag = Tags.query.get_or_404(tag_id)
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 12

    # 获取含有该标签的电影
    query = Movie.query.filter(Movie.tags.any(id=tag_id))
    total = query.count()
    movies = query.paginate(page=page, per_page=per_page, error_out=False).items

    pagination = Pagination(page=page, total=total, per_page=per_page,
                            css_framework='bootstrap4')

    return render_template('user/items.html',
                           movies=movies,
                           title=f'Tag: {tag.name}',
                           pagination=pagination)


@movie_bp.route('/hot')
def hot_movie():
    print("进入hot_movie函数")
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 12

    # 简化为直接查询所有电影
    query = Movie.query
    
    print("查询构建完成")
    total = query.count()
    print(f"总电影数: {total}")
    
    # 使用标准分页方式
    movies = query.paginate(page=page, per_page=per_page, error_out=False).items
    print(f"获取到的电影数: {len(movies)}")

    pagination = Pagination(page=page, total=total, per_page=per_page,
                            css_framework='bootstrap4')

    return render_template('user/items.html',
                           movies=movies,
                           title='Popular Movies',
                           pagination=pagination)


@movie_bp.route('/most_mark')
def most_mark():
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 12

    # 按评分数量排序
    rate_count = func.count(Rate.id).label('rate_count')
    query = db.session.query(Movie, rate_count) \
        .outerjoin(Rate) \
        .group_by(Movie.id) \
        .order_by(desc(rate_count))

    # 获取总数
    total = query.count()
    
    # 获取分页数据
    results = query.limit(per_page).offset((page-1)*per_page).all()
    movies = [m[0] for m in results]

    pagination = Pagination(page=page, total=total, per_page=per_page,
                            css_framework='bootstrap4')

    return render_template('user/items.html',
                           movies=movies,
                           title='Most Rated',
                           pagination=pagination)


@movie_bp.route('/most_view')
def most_view():
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 12

    # 按浏览量排序
    query = Movie.query.order_by(Movie.num.desc())

    total = query.count()
    movies = query.paginate(page=page, per_page=per_page, error_out=False).items

    pagination = Pagination(page=page, total=total, per_page=per_page,
                            css_framework='bootstrap4')

    return render_template('user/items.html',
                           movies=movies,
                           title='Most Viewed',
                           pagination=pagination)


@movie_bp.route('/latest')
def latest_movie():
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 12

    # 按年份排序
    query = Movie.query.order_by(Movie.years.desc())

    total = query.count()
    movies = query.paginate(page=page, per_page=per_page, error_out=False).items

    pagination = Pagination(page=page, total=total, per_page=per_page,
                            css_framework='bootstrap4')

    return render_template('user/items.html',
                           movies=movies,
                           title='Latest Movies',
                           pagination=pagination)


@movie_bp.route('/director/<director_name>')
def director_movies(director_name):
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 12

    # 查询导演的电影
    query = Movie.query.filter(Movie.director == director_name)

    total = query.count()
    movies = query.paginate(page=page, per_page=per_page, error_out=False).items

    pagination = Pagination(page=page, total=total, per_page=per_page,
                            css_framework='bootstrap4')

    return render_template('user/items.html',
                           movies=movies,
                           title=f'Movies by {director_name}',
                           pagination=pagination)


@movie_bp.route('/user_recommend')
@login_required
def user_recommend():
    user_id = session.get('user_id')
    movies = recommend_by_user_id(user_id, 12)
    return render_template('user/items.html',
                           movies=movies,
                           title='User-based Recommendations')


@movie_bp.route('/item_recommend')
@login_required
def item_recommend():
    user_id = session.get('user_id')
    movies = recommend_by_item_id(user_id, 12)
    return render_template('user/items.html',
                           movies=movies,
                           title='Item-based Recommendations')


@movie_bp.route('/ajax/user_recommend')
@login_required
def ajax_user_recommend():
    user_id = session.get('user_id')
    movies = recommend_by_user_id(user_id, 4)
    movie_data = []

    for movie in movies:
        tag_names = [tag.name for tag in movie.tags]
        movie_data.append({
            'id': movie.id,
            'name': movie.name,
            'image_link': movie.image_link,
            'tags': tag_names,
            'tags_display': ', '.join(tag_names),
            'collect_count': len(movie.collect),
            'years': movie.years.strftime('%Y-%m-%d')
        })

    return jsonify(movie_data)


@movie_bp.route('/ajax/item_recommend')
@login_required
def ajax_item_recommend():
    user_id = session.get('user_id')
    movies = recommend_by_item_id(user_id, 4)
    movie_data = []

    for movie in movies:
        tag_names = [tag.name for tag in movie.tags]
        movie_data.append({
            'id': movie.id,
            'name': movie.name,
            'image_link': movie.image_link,
            'tags': tag_names,
            'tags_display': ', '.join(tag_names),
            'collect_count': len(movie.collect),
            'years': movie.years.strftime('%Y-%m-%d')
        })

    return jsonify(movie_data)


@movie_bp.route('/analytics')
def analytics_dashboard():
    return render_template('user/analytics_dashboard.html')


@movie_bp.route('/api/tag_distribution')
def tag_distribution_api():
    # 获取标签分布数据
    tag_data = db.session.query(Tags.name, func.count(Movie.id).label('movie_count')) \
        .join(Movie.tags) \
        .group_by(Tags.id) \
        .order_by(desc('movie_count')) \
        .all()
        # .limit(10) \
        

    result = []
    for tag in tag_data:
        result.append({
            'name': tag[0],
            'movie_count': tag[1]
        })

    return jsonify(result)


@movie_bp.route('/api/tag_ratings')
def tag_ratings_api():
    # 获取标签平均评分数据
    tag_ratings = db.session.query(Tags.name, func.avg(Rate.mark).label('avg_rating')) \
        .join(Movie.tags) \
        .join(Rate, Rate.movie_id == Movie.id) \
        .group_by(Tags.id) \
        .order_by(desc('avg_rating')) \
        .limit(20) \
        .all()

    result = []
    for tag in tag_ratings:
        result.append({
            'name': tag[0],
            'avg_rating': float(tag[1]) if tag[1] else 0
        })

    return jsonify(result)


@movie_bp.route('/api/top_rated_movies')
def top_rated_movies_api():
    # 获取评分最高的电影
    top_movies = db.session.query(Movie.name, func.avg(Rate.mark).label('avg_rating'), func.count(Rate.id).label('rating_count')) \
        .join(Rate).group_by(Movie.id).having(func.count(Rate.id) >= 3).order_by(desc('avg_rating')).limit(20).all()

    result = []
    for movie in top_movies:
        result.append({
            'name': movie[0],
            'avg_rating': float(movie[1]),
            'rating_count': movie[2]
        })

    return jsonify(result)


@movie_bp.route('/api/latest_movies')
def latest_movie_api():
    # 获取最新电影
    movies = Movie.query.order_by(Movie.years.desc()).limit(8).all()
    movie_data = []

    for movie in movies:
        tag_names = [tag.name for tag in movie.tags]
        movie_data.append({
            'id': movie.id,
            'name': movie.name,
            'image_link': movie.image_link,
            'tags_display': ', '.join(tag_names),
            'collect_count': len(movie.collect),
            'years': movie.years.strftime('%Y-%m-%d')
        })

    return jsonify(movie_data)


@movie_bp.route('/api/check_login')
def check_login_api():
    """检查用户登录状态的API"""
    is_logged_in = session.get('login_in', False)
    user_id = session.get('user_id', None)
    username = session.get('name', '')
    
    return jsonify({
        'is_logged_in': is_logged_in,
        'user_id': user_id,
        'username': username
    })
