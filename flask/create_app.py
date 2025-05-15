from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from datetime import timedelta
import os
import secrets

# 创建全局数据库对象
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()

def create_app():
    # 创建Flask应用
    app = Flask(__name__)
    app.config['SECRET_KEY'] = secrets.token_hex(16)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'media')
    app.config['MEDIA_URL'] = '/media/'

    # 设置会话配置
    app.config['SESSION_COOKIE_SECURE'] = False  # 开发环境设为False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    # 配置WTF CSRF
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1小时
    app.config['WTF_CSRF_SSL_STRICT'] = False  # 不要求HTTPS

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # 注册自定义过滤器
    from utils.filters import register_filters
    register_filters(app)

    # 导入模型 (只导入，不使用)
    from models.models import User, Movie, Tags, Rate, Comment, LikeComment, UserTagPrefer, SharedRecommendation, MovieUpload

    # 导入路由蓝图
    from routes.auth import auth_bp
    from routes.movie import movie_bp
    from routes.user import user_bp
    from routes.admin import admin_bp

    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(movie_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)

    # Jinja2模板设置
    app.jinja_env.globals.update(enumerate=enumerate, len=len)

    # 上下文处理器
    @app.context_processor
    def utility_processor():
        return {'MEDIA_URL': app.config['MEDIA_URL']}

    # 添加获取当前用户的上下文处理器
    @app.context_processor
    def inject_user():
        from flask import session
        from models.models import User
        if session.get('login_in') and session.get('user_id'):
            user = User.query.get(session.get('user_id'))
            return dict(user=user)
        return dict(user=None)

    # 配置媒体文件服务
    @app.route('/media/<path:filename>')
    def serve_media(filename):
        from flask import send_from_directory
        # 分离目录和文件名
        directory, file = os.path.split(filename)
        media_path = os.path.join('../media', directory)
        return send_from_directory(media_path, file)

    # 创建默认管理员账户
    def create_default_admin():
        from models.models import User
        # 检查是否已存在用户名为admin的账户
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                password='admin123',  # 在生产环境中应该使用更安全的密码
                email='admin@example.com'
            )
            db.session.add(admin)
            db.session.commit()
            print('Default admin account created: admin/admin123')
        else:
            print('Admin account already exists')

    # 创建数据库表
    with app.app_context():
        db.create_all()
        create_default_admin()

    return app 