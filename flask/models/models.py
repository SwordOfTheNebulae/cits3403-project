from flask import current_app
from datetime import datetime, date
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func
from app.create_app import db

# 用户和电影的多对多关系表 - 收藏关系
movie_collectors = db.Table('movie_collectors',
    db.Column('movie_id', db.Integer, db.ForeignKey('movie.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

# 电影和标签的多对多关系表
movie_tags = db.Table('movie_tags',
    db.Column('movie_id', db.Integer, db.ForeignKey('movie.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)

# 分享和用户的多对多关系表
shared_with_users = db.Table('shared_with_users',
    db.Column('share_id', db.Integer, db.ForeignKey('shared_recommendation.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

# 分享和电影的多对多关系表
shared_movies = db.Table('shared_movies',
    db.Column('share_id', db.Integer, db.ForeignKey('shared_recommendation.id'), primary_key=True),
    db.Column('movie_id', db.Integer, db.ForeignKey('movie.id'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    created_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 反向关系
    rates = db.relationship('Rate', backref='user', lazy='dynamic')
    comments = db.relationship('Comment', backref='user', lazy='dynamic')
    like_comments = db.relationship('LikeComment', backref='user', lazy='dynamic')
    tag_prefers = db.relationship('UserTagPrefer', backref='user', lazy='dynamic')
    movie_uploads = db.relationship('MovieUpload', backref='user', lazy='dynamic')
    shared_recommendations = db.relationship('SharedRecommendation', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return self.username

class Tags(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    
    # 反向关系
    tag_prefers = db.relationship('UserTagPrefer', backref='tag', lazy='dynamic')
    
    def __repr__(self):
        return self.name

class UserTagPrefer(db.Model):
    __tablename__ = 'user_tag_prefer'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), nullable=False)
    score = db.Column(db.Float, default=0)
    
    def __repr__(self):
        return f"{self.user.username}: {self.score}"

class Movie(db.Model):
    __tablename__ = 'movie'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    director = db.Column(db.String(255), nullable=False)
    country = db.Column(db.String(255), nullable=False)
    years = db.Column(db.Date, nullable=False)
    leader = db.Column(db.String(1024), nullable=False)
    d_rate_nums = db.Column(db.Integer, nullable=False)
    d_rate = db.Column(db.String(255), nullable=False)
    intro = db.Column(db.Text, nullable=False)
    num = db.Column(db.Integer, default=0)
    origin_image_link = db.Column(db.String(255), nullable=True)
    image_link = db.Column(db.String(255), nullable=False)
    imdb_link = db.Column(db.String(255), nullable=True)
    douban_link = db.Column(db.String(255), nullable=False)
    douban_id = db.Column(db.String(128), nullable=True)
    
    # 多对多关系
    tags = db.relationship('Tags', secondary=movie_tags, lazy='subquery',
                           backref=db.backref('movies', lazy=True))
    collect = db.relationship('User', secondary=movie_collectors, lazy='subquery',
                              backref=db.backref('collected_movies', lazy=True))
    
    # 反向关系
    rates = db.relationship('Rate', backref='movie', lazy='dynamic')
    comments = db.relationship('Comment', backref='movie', lazy='dynamic')
    
    @property
    def movie_rate(self):
        avg_rate = db.session.query(func.avg(Rate.mark)).filter(Rate.movie_id == self.id).scalar()
        return avg_rate if avg_rate else 'None'
    
    def to_dict(self, fields=None, exclude=None):
        data = {}
        for c in self.__table__.columns:
            if exclude and c.name in exclude:
                continue
            if fields and c.name not in fields:
                continue
            value = getattr(self, c.name)
            if isinstance(value, date):
                value = value.strftime('%Y-%m-%d')
            data[c.name] = value
        return data
    
    def __repr__(self):
        return self.name

class MovieUpload(db.Model):
    __tablename__ = 'movie_upload'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    csv_file = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="pending")
    processed_count = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f"{self.user.username}'s upload at {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"

class Rate(db.Model):
    __tablename__ = 'rate'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mark = db.Column(db.Float, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def avg_mark(self):
        return db.session.query(func.avg(Rate.mark)).scalar()
    
    def __repr__(self):
        return f"{self.user.username} rated {self.movie.name}: {self.mark}"

class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(255), nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    
    # 反向关系
    likes = db.relationship('LikeComment', backref='comment', lazy='dynamic')
    
    def __repr__(self):
        return f"Comment by {self.user.username} on {self.movie.name}"

class LikeComment(db.Model):
    __tablename__ = 'like_comment'
    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f"{self.user.username} liked comment {self.comment_id}"

class SharedRecommendation(db.Model):
    __tablename__ = 'shared_recommendation'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    share_key = db.Column(db.String(64), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=False)
    
    # 多对多关系
    movies = db.relationship('Movie', secondary=shared_movies, lazy='subquery',
                             backref=db.backref('in_shared', lazy=True))
    shared_with = db.relationship('User', secondary=shared_with_users, lazy='subquery',
                                  backref=db.backref('shared_to_me', lazy=True))
    
    def __repr__(self):
        return f"{self.user.username}'s share: {self.title}" 
