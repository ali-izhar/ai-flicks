import os
from flask import request, render_template, redirect, url_for, flash, session, Blueprint
from flask_login import current_user, login_user, logout_user
from google_auth_oauthlib.flow import Flow
from app.services import get_user_by_email, create_user
from app.utils import allowed_file
import logging
from utils import resize_avatar, generate_random_password, get_google_profile_pic

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        user = get_user_by_email(request.form.get('email').strip())
        if user and user.check_password(request.form.get('password').strip()):
            login_user(user, remember=True)
            if 'plan_name' in session:
                return redirect(url_for('aiflix_user.create_checkout_session', plan_name=session.get('plan_name')))
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('Successfully logged out. See you again soon!')
    return redirect(url_for('auth.login'))

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email').strip()
        password = request.form.get('password').strip()
        avatar = request.files['avatar']

        # Validate input
        if not all([email, password]):
            flash('Please enter all the fields')
            return redirect(url_for('auth.signup'))

        existing_user = get_user_by_email(email)
        if existing_user:
            flash('An account with that email already exists. Please login.')
            return redirect(url_for('auth.login'))

        existing_username = get_user_by_email(email)
        if existing_username:
            flash('That username is already taken. Please choose a different username.')
            return redirect(url_for('auth.signup'))
        
        # Resize and save the avatar
        if avatar and allowed_file(avatar.filename):
            try:
                resized_avatar = resize_avatar(avatar.read())
            except Exception as e:
                logging.error("Error resizing avatar: ", e)
                resized_avatar = None
        
        if not avatar or resized_avatar is None:
            with open('app/static/img/icons/default.png', 'rb') as img:
                resized_avatar = img.read()

        new_user = create_user(email, password, resized_avatar)
        login_user(new_user)
        flash('Your account has been created!')
        if 'plan_name' in session:
            return redirect(url_for('aiflix_user.create_checkout_session', plan_name=session.get('plan_name')))
        return redirect(url_for('main.index'))
    return render_template('signup.html')

@auth_bp.route('/login/google')
def google_login():
    google_auth = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": os.getenv('GOOGLE_CLIENT_KEY'),
                "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [url_for('auth.google_auth', _external=True, _scheme='https')]
            }
        },
        scopes=['https://www.googleapis.com/auth/userinfo.profile',
                'https://www.googleapis.com/auth/userinfo.email']
    )

    redirect_uri = url_for('auth.google_auth', _external=True)
    google_auth.redirect_uri = redirect_uri
    authorization_url, state = google_auth.authorization_url()

    session['oauth_state'] = state
    return redirect(authorization_url)

@auth_bp.route('/login/google/auth')
def google_auth():
    state = session.get('oauth_state')
    if state is None:
        return redirect(url_for('auth.login'))

    google_auth = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": os.getenv('GOOGLE_CLIENT_KEY'),
                "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [url_for('auth.google_auth', _external=True, _scheme='https')]
            }
        },
        scopes=['openid', 'https://www.googleapis.com/auth/userinfo.profile',
                'https://www.googleapis.com/auth/userinfo.email'],
        state=state
    )

    google_auth.redirect_uri = url_for('auth.google_auth', _external=True)
    
    # Ensure that we got back the same state to avoid CSRF attacks
    if state != request.args.get('state', ''):
        return redirect(url_for('auth.login'))
    
    google_auth.fetch_token(
        authorization_response_url=request.url,
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        code=request.args.get('code')
    )

    userinfo = google_auth.authorized_session().get('https://www.googleapis.com/oauth2/v1/userinfo').json()

    email = userinfo['email'] 
    avatar = userinfo['picture']
    avatar = get_google_profile_pic(avatar)
    resized_avatar = resize_avatar(avatar)

    existing_user = get_user_by_email(email)
    if existing_user:
        login_user(existing_user)
        return redirect(url_for('main.index'))

    new_user = create_user(
        email=email,
        password=generate_random_password(),
        avatar=resized_avatar
    )

    login_user(new_user)
    return redirect(url_for('main.index'))