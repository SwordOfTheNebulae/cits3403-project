import hashlib
import urllib.parse
from flask import current_app
from datetime import datetime

def gravatar(email, size=100, default='identicon', rating='g'):
    """生成Gravatar头像URL"""
    url = "https://www.gravatar.com/avatar/"
    hash_value = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
    return f"{url}{hash_value}?{urllib.parse.urlencode({'d': default, 's': str(size), 'r': rating})}"

def format_datetime(value, format='%Y-%m-%d %H:%M'):
    """格式化日期时间"""
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                value = datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                return value
    
    return value.strftime(format)

def register_filters(app):
    """在Flask应用中注册过滤器"""
    app.jinja_env.filters['gravatar'] = gravatar
    app.jinja_env.filters['datetime'] = format_datetime
    
    # 添加strftime过滤器
    def strftime_filter(date, format='%Y-%m-%d'):
        """将日期格式化为字符串"""
        if date is None:
            return ""
        return date.strftime(format)
        
    app.jinja_env.filters['strftime'] = strftime_filter 