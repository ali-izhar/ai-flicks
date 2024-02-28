import os
import random
import base64
import traceback
from flask import request, render_template, abort, jsonify, Blueprint
from flask_login import current_user
from app.api import Model, ModelError
from app.data import PROMPTS
from openai import OpenAI
import logging

gallery_bp = Blueprint('gallery', __name__, url_prefix='/gallery')

openai_client = OpenAI()

HUGGING_FACE_API_URLS = {
    'stable-diffusion-v15': os.getenv('STABLE_DIFFUSION_V15'),
    'stable-diffusion-v21': os.getenv('STABLE_DIFFUSION_V21'),
    'stable-diffusion-xl-base-0.9': os.getenv('STABLE_DIFFUSION_XL_BASE_0.9'),
    'stable-diffusion-xl-base-1.0': os.getenv('STABLE_DIFFUSION_XL_BASE_1.0'),
    'dreamlike-photo-real': os.getenv('DREAMLIKE_PHOTO_REAL'),
    'dream-shaper': os.getenv('DREAM_SHAPER'),
    'realistic-vision-v14': os.getenv('REALISTIC_VISION_V14'),
    'nitro-diffusion': os.getenv('NITRO_DIFFUSION'),
    'dreamlike-anime': os.getenv('DREAMLIKE_ANIME_V10'),
    'anything-v5': os.getenv('ANYTHING_V5'),
}

@gallery_bp.route('/')
def gallery():
    exclude_images = ['forest.png', 'hoodie-b.png', 'hoodie-w.png', 'tshirt-b.png', 'tshirt-w.png', 'logo.png']
    images = [f for f in os.listdir('app/static/img') if f.endswith('.png') and f not in exclude_images]
    return render_template('gallery.html', images=images, user=current_user)

@gallery_bp.route('/model', methods=['POST'])
def model():
    logging.info("[Function: model] Received request")

    try:
        data = request.form
        prompt = data.get('prompt')
        if not prompt:
            return abort(400, "Invalid form data supplied")
    except TimeoutError as te:
        logging.error(f"[Function: model] Timeout error occurred: {te}")
        return render_template('error.html', error='Timeout')
    except Exception as e:
        logging.error(f"[Function: model] Error occurred: {e}")
        traceback.print_exc()
        return render_template('error.html', error=str(e))
    
    generate_with_dalle = True

    if generate_with_dalle:
        image = dalle_model(prompt)
        return render_template('result.html', image=image, prompt=prompt, user=current_user)
    else:
        model_input = data.get('model_input')
        selected_model = HUGGING_FACE_API_URLS.get(model_input)
        negative_prompt = data.get('negative_prompt')

        if not selected_model:
            return abort(400, "Invalid form data supplied")

        if not negative_prompt or negative_prompt.isspace():
            negative_prompt = get_negative_prompt(selected_model, prompt)
        return generate_image(selected_model, prompt, negative_prompt)

def dalle_model(prompt, model='dall-e-3'):
    try:
        response = openai_client.images.generate(
            model=model,
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        return image_url
    except Exception as e:
        logging.error(f"[Function: dalle_model] Error occurred: {e}")
        traceback.print_exc()
        return render_template('error.html', error=str(e))

def generate_image(selected_model, prompt, negative_prompt):
    for attempt in range(3):
        try:
            logging.info(f"[Function: generate_image] Attempt {attempt + 1}")
            image = query_model(selected_model, prompt, negative_prompt)
        except ModelError as e:
            if attempt < 2: # Only allow retries if less than 2 attempts have been made
                logging.info(f"[Function: generate_image] Attempt {attempt + 1} failed: {e}")
                continue
            else:
                return render_template('error.html', error=str(e))
        image_data = f"data:image/png;base64,{image}"
        return render_template('result.html', image=image_data, prompt=prompt, user=current_user)
    return render_template('error.html', error='No image generated after retries')

def query_model(selected_model, prompt, negative_prompt):
    model = Model(selected_model, prompt, negative_prompt, 7, 20, 1024, 1024)
    try:
        logging.info(f"[Function: query_model] Querying model")
        image = model.generate()
    except TimeoutError:
        raise ModelError('Timeout while generating image')

    if not image:
        raise ModelError('No image generated')
    return image

@gallery_bp.route('/gallery_image/<path:img_name>', methods=['GET'])
def gallery_image(img_name):
    try:
        file_path = f"app/static/img/{img_name}"
        with open(file_path, "rb") as img_file:
            image = base64.b64encode(img_file.read()).decode('utf-8')
        image_data = f"data:image/png;base64,{image}"
        return render_template("result.html", image=image_data, prompt="Gallery Image", user=current_user)
    except Exception as e:
        logging.error(f"[Function: gallery_image] Error serving image: {e}")
        return render_template("error.html")

@gallery_bp.route('/random-prompt', methods=['GET'])
def random_prompt():
    selected_model = request.args.get('model')
    try:
        prompt = random.choice(PROMPTS[selected_model])["prompt"]
    except KeyError:
        return abort(400, "Invalid model name supplied")
    return jsonify({'prompt': prompt})

def get_negative_prompt(model, given_prompt):
    prompt_list = PROMPTS.get(model)
    if not prompt_list:
        return None
    for prompt_dict in prompt_list:
        if prompt_dict['prompt'] == given_prompt:
            return prompt_dict['negative_prompt']
    return ""
