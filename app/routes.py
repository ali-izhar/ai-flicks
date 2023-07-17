import asyncio
import os
import base64
from flask import request, render_template, abort, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user, login_user, logout_user
from concurrent.futures import TimeoutError

from app import app, login_manager
from .db_ops import *

from model import Model, ModelError
from utils import generate_negative_prompt, generate_random_prompt, resize_avatar


HUGGING_FACE_API_URLS = {
    'stable-diffusion': os.environ.get('HUGGING_FACE_API_URL1'),
    'realistic-vision': os.environ.get('HUGGING_FACE_API_URL2'),
    'nitro-diffusion': os.environ.get('HUGGING_FACE_API_URL3'),
    'dreamlike-anime': os.environ.get('HUGGING_FACE_API_URL4'),
}


@login_manager.unauthorized_handler
def unauthorized():
    flash('You must be logged in to view this page.')
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    session.permanent = False
    return render_template("index.html", user=current_user)


@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(403)
    return render_template('admin_profile.html', user=current_user)


@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        abort(403)
    users = get_all_users()
    return render_template('admin_users.html', user=current_user, users=users)
    

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        user = get_by_username(request.form.get('username').strip())
        if user and user.check_password(request.form.get('password').strip()):
            login_user(user, remember=True)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    flash('Successfully logged out. See you again soon!')
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        first_name = request.form.get('first_name').strip()
        last_name = request.form.get('last_name').strip()
        username = request.form.get('username').strip()
        email = request.form.get('email').strip()
        password = request.form.get('password').strip()
        avatar = request.files['avatar']

        # Validate input
        if not all([first_name, last_name, username, email, password]):
            flash('Please enter all the fields')
            return redirect(url_for('signup'))

        existing_user = get_by_email(email)
        if existing_user:
            flash('An account with that email already exists. Please login.')
            return redirect(url_for('login'))

        existing_username = get_by_username(username)
        if existing_username:
            flash('That username is already taken. Please choose a different username.')
            return redirect(url_for('signup'))
        
        # Resize and save the avatar
        if avatar and allowed_file(avatar.filename):
            try:
                resized_avatar = resize_avatar(avatar.read())
            except Exception as e:
                print("Error resizing avatar: ", e)
                resized_avatar = None
        
        if not avatar or resized_avatar is None:
            with open('app/frontend/assets/img/default.png', 'rb') as img:
                resized_avatar = img.read()

        create_user(first_name, last_name, email, username, password, resized_avatar)
        flash('Your account has been created! You can now login.')
        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/pricing')
def pricing():
    return render_template('pricing.html')


@app.route('/models')
def models():
    return render_template('models.html', user=current_user)


@app.route('/guide')
def guide():
    return render_template('guide.html', user=current_user)


@app.route('/gallery')
def gallery():
    exclude_images = ['forest.png', 'hoodie-b.png', 'hoodie-w.png', 'tshirt-b.png', 'tshirt-w.png', 'logo.png']
    images = [f for f in os.listdir('app/frontend/assets/img') if f.endswith('.png') and f not in exclude_images]
    return render_template('gallery.html', images=images, user=current_user)


@app.route('/model', methods=['POST'])
async def model():
    try:
        data = request.form
        model_input = data.get('model_input')
        selected_model = HUGGING_FACE_API_URLS.get(model_input)
        prompt = data.get('prompt')
        negative_prompt = data.get('negative_prompt')

        if not selected_model or not prompt:
            return abort(400, "Invalid form data supplied")
        
        if not negative_prompt or negative_prompt.isspace():
            negative_prompt = generate_negative_prompt(model_input)
        return await generate_image(selected_model, prompt, negative_prompt)

    except TimeoutError:
        return render_template('error.html', error='Timeout')

    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        return render_template('error.html', error=str(e))
    

async def generate_image(selected_model, prompt, negative_prompt):
    for attempt in range(3):
        try:
            image = await query_model(selected_model, prompt, negative_prompt)
        except ModelError as e:
            if attempt < 2: # Only allow retries if less than 2 attempts have been made
                print(f"Attempt {attempt + 1} failed: {e}")
                continue
            else:
                return render_template('error.html', error=str(e))
        image_data = f"data:image/png;base64,{image}"
        return render_template('result.html', image=image_data, prompt=prompt, user=current_user)
    return render_template('error.html', error='No image generated after retries')


async def query_model(selected_model, prompt, negative_prompt):
    model = Model(selected_model, prompt, negative_prompt)
    try:
        image = await asyncio.wait_for(model.generate(), timeout=120)
    except TimeoutError:
        raise ModelError('Timeout while generating image')

    if not image:
        raise ModelError('No image generated')
    return image


@app.route('/gallery-image/<path:img_name>', methods=['GET'])
def gallery_image(img_name):
    try:
        file_path = f"app/frontend/assets/img/{img_name}"
        with open(file_path, "rb") as img_file:
            image = base64.b64encode(img_file.read()).decode('utf-8')
        image_data = f"data:image/png;base64,{image}"
        return render_template("result.html", image=image_data, prompt="Gallery Image", user=current_user)
    except Exception as e:
        print(f"Error serving image: {e}")
        return render_template("error.html")


@app.route('/random-prompt', methods=['GET'])
def random_prompt():
    selected_model = request.args.get('model')
    prompt = generate_random_prompt(selected_model)
    return jsonify({'prompt': prompt})


def allowed_file(filename):
    ALLOWED_EXTENSIONS = app.config['ALLOWED_EXTENSIONS']
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS 