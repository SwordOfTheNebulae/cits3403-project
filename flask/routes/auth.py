from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from create_app import db
from models.models import User, Tags, UserTagPrefer
from utils.forms import LoginForm, RegisterForm, TagPreferForm
from utils.decorators import login_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('login_in'):
        return redirect(url_for('movie.index'))

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            # 设置会话为永久
            session.permanent = True
            # 登录成功，设置session
            session['login_in'] = True
            session['user_id'] = user.id
            session['name'] = username

            # 检查是否是新用户首次注册
            new = session.get('new')
            if new:
                tags = Tags.query.all()
                return render_template('user/choose_tag.html', tags=tags)

            return redirect(url_for('movie.index'))
        else:
            if user:
                flash('Incorrect password', 'danger')
            else:
                flash('User does not exist', 'danger')

    return render_template('user/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password2.data
        email = form.email.data

        # 创建新用户
        user = User(username=username, password=password, email=email)
        db.session.add(user)
        db.session.commit()

        # 设置session标记为新用户
        session['new'] = 'true'
        flash('Registration successful, please login', 'success')
        return redirect(url_for('auth.login'))

    return render_template('user/register.html', form=form)


@auth_bp.route('/logout')
def logout():
    if not session.get('login_in'):
        return redirect(url_for('movie.index'))

    # 清除session
    session.clear()
    flash('You have successfully logged out', 'success')
    return redirect(url_for('movie.index'))


@auth_bp.route('/choose_tags', methods=['GET', 'POST'])
@login_required
def choose_tags():
    form = TagPreferForm()

    if form.validate_on_submit():
        user_id = session.get('user_id')
        selected_tags = form.tags.data

        # 清除用户之前的标签偏好
        UserTagPrefer.query.filter_by(user_id=user_id).delete()

        # 添加新的标签偏好
        for tag_id in selected_tags:
            tag_prefer = UserTagPrefer(user_id=user_id, tag_id=tag_id, score=1.0)
            db.session.add(tag_prefer)

        db.session.commit()

        # 清除新用户标记
        session.pop('new', None)

        flash('Tags selected successfully', 'success')
        return redirect(url_for('movie.index'))

    return render_template('user/choose_tag.html', form=form, tags=Tags.query.all())
