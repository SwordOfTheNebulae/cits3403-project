from functools import wraps
from flask import session, redirect, url_for, flash, request, abort

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('login_in'):
            flash('please login', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('login_in'):
            flash('please login', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        if session.get('user_id') != 1:  # 假设ID为1的用户是管理员
            abort(403)
        return f(*args, **kwargs)
    return decorated_function 