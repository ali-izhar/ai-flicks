import os
import base64
import time
from flask import render_template, request, jsonify, session, abort
from utils import generate_random_prompt, generate_negative_prompt
from model import Model
from app import app


HUGGING_FACE_API_URLS = {
    'stable-diffusion': os.environ.get('HUGGING_FACE_API_URL1'),
    'realistic-vision': os.environ.get('HUGGING_FACE_API_URL2'),
    'nitro-diffusion': os.environ.get('HUGGING_FACE_API_URL3'),
    'dreamlike-anime': os.environ.get('HUGGING_FACE_API_URL4'),
}


@app.route('/')
def index():
    session.permanent = False
    return render_template("index.html")


@app.route('/models')
def models():
    return render_template('models.html')


@app.route('/guide')
def guide():
    return render_template('guide.html')


@app.route('/gallery')
def gallery():
    exclude_images = ['forest.png', 'hoodie-b.png', 'hoodie-w.png', 'tshirt-b.png', 'tshirt-w.png', 'logo.png']
    images = [f for f in os.listdir('app/frontend/assets/img') if f.endswith('.png') and f not in exclude_images]
    return render_template('gallery.html', images=images)


@app.route('/model', methods=['POST'])
def model():
    data = request.form
    selected_model = data.get('model_input')
    prompt = data.get('prompt')
    negative_prompt = data.get('negative_prompt')

    if not selected_model or not prompt:
        return abort(400, "Invalid form data supplied")

    HUGGING_API = HUGGING_FACE_API_URLS.get(selected_model)
    if not HUGGING_API:
        return abort(400, "Invalid model selected")

    if not negative_prompt or negative_prompt.isspace():
        negative_prompt = generate_negative_prompt(selected_model)

    return generate_image_and_render(HUGGING_API, selected_model, prompt, negative_prompt)


def generate_image_and_render(HUGGING_API, selected_model, prompt, negative_prompt, retry_count=0):
    model = Model(HUGGING_API, prompt=prompt, negative_prompt=negative_prompt)

    print("Prompt: ", prompt)
    print("Negative Prompt: ", negative_prompt)
    print("Model: ", selected_model)
    print("Hugging Face API: ", HUGGING_API)

    try:
        start = time.time()
        response = model.generate_image()
        print(f"Time taken: {time.time() - start} seconds")
        if response == "timeout" and retry_count < 5:  # Limit retries to avoid infinite recursion
            print('retrying...')
            return generate_image_and_render(HUGGING_API, selected_model, prompt, negative_prompt, retry_count + 1)
    except Exception as e:
        return render_template("error.html", error=str(e))

    if not response or response == "timeout":
        return render_template("error.html", error="No image generated or timeout after retries")
    
    image_data = f"data:image/png;base64,{response}"
    return render_template("result.html", image=image_data, prompt=prompt)


@app.route('/gallery-image/<img_name>', methods=['GET'])
def gallery_image(img_name):
    try:
        file_path = f"app/frontend/assets/img/{img_name}"
        print(f"Fetching image from: {file_path}")
        with open(file_path, "rb") as img_file:
            image = base64.b64encode(img_file.read()).decode('utf-8')
        image_data = f"data:image/png;base64,{image}"
        return render_template("result.html", image=image_data, prompt="Gallery Image")
    except Exception as e:
        print(f"Error serving image: {e}")
        return render_template("error.html")


@app.route('/random-prompt', methods=['GET'])
def random_prompt():
    selected_model = request.args.get('model')
    prompt = generate_random_prompt(selected_model)
    return jsonify({'prompt': prompt})