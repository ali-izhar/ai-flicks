import os
import base64
import time
from flask import render_template, request, jsonify, url_for, redirect, session, abort, current_app
from utils import generate_random_prompt, generate_negative_prompt, send_email, Tshirt, Hoodie
from model import Model
from app import app
import stripe


HUGGING_FACE_API_URLS = {
    'stable-diffusion': os.environ.get('HUGGING_FACE_API_URL1'),
    'realistic-vision': os.environ.get('HUGGING_FACE_API_URL2'),
    'nitro-diffusion': os.environ.get('HUGGING_FACE_API_URL3'),
    'dreamlike-anime': os.environ.get('HUGGING_FACE_API_URL4'),
}

base_64_url = None

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


@app.route('/cart')
def cart():
    cart = session.get('cart', [])

    if not cart:
        return render_template('cart.html', cart_items=cart, subtotal=0)
    
    subtotal = sum(item['price'] * item['quantity'] for item in cart)
    return render_template('cart.html', cart_items=cart, subtotal=subtotal)


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
    
    base_64_url = response
    return render_template("result.html", image=response, prompt=prompt)

@app.route('/teemill', methods=['GET'])
def teemill_render():
    return render_template("teemill.html", image=base_64_url)


@app.route('/gallery-image/<img_name>', methods=['GET'])
def gallery_image(img_name):
    try:
        file_path = f"app/frontend/assets/img/{img_name}"
        with open(file_path, "rb") as img_file:
            image = base64.b64encode(img_file.read()).decode('utf-8')
        return render_template("result.html", image=image, prompt="Gallery Image")
    except Exception as e:
        print(f"Error serving image: {e}")
        return render_template("error.html")


@app.route('/random-prompt', methods=['GET'])
def random_prompt():
    selected_model = request.args.get('model')
    prompt = generate_random_prompt(selected_model)
    return jsonify({'prompt': prompt})


@app.route('/addToCart', methods=['POST'])
def addToCart():
    image_base64 = request.form.get('imageBase64')
    selectedProduct = request.form.get('selectedProduct')
    quantity = int(request.form.get('quantity', 1)) 

    # Dictionary to determine product type
    products = {
        'tshirt': Tshirt,
        'hoodie': Hoodie
    }

    if selectedProduct in products:
        selectedSize = request.form.get(f'{selectedProduct}SelectedSize')
        selectedColor = request.form.get(f'{selectedProduct}SelectedColor')
        price = 20.00 if selectedProduct == 'tshirt' else 40.00
        product = products[selectedProduct]("Your {} design".format(selectedProduct), selectedSize, selectedColor, image_base64, price, quantity)
    else:
        return abort(400, "Invalid product type")

    cart = session.get('cart', [])
    cart.append(product.to_dict())
    session['cart'] = cart
    return redirect(url_for('cart'))


@app.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    data = request.get_json()
    product_id = data.get('productId', None)
    cart = session.get('cart', [])

    for item in cart:
        if item['id'] == product_id:
            cart.remove(item)
            break

    session['cart'] = cart
    return jsonify({"success": True}), 200


@app.route('/update_cart_quantity', methods=['POST'])
def update_cart_quantity():
    data = request.get_json()
    product_id = data.get('productId', None)
    new_quantity = int(data.get('newQuantity', 1))
    cart = session.get('cart', [])

    new_total = 0.0
    subtotal = 0.0
    for item in cart:
        if item['id'] == product_id:
            item['quantity'] = new_quantity
            new_total = item['price'] * new_quantity
        subtotal += item['price'] * item['quantity']

    session['cart'] = cart

    return jsonify({"success": True, "newTotal": new_total, "subtotal": subtotal}), 200


@app.route('/create_checkout_session', methods=['POST'])
def create_checkout_session():
    cart = session.get('cart', [])
    if not cart:
        return abort(400, "Cart is empty")

    line_items = [{
        'price_data': {
            'currency': 'usd',
            'unit_amount': int(float(product['price']) * 100),
            'product_data': {
                'name': product['name'],
            },
        },
        'quantity': product['quantity'],
    } for product in cart]

    try:
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            shipping_address_collection={
                'allowed_countries': ['US'],
            },
            billing_address_collection='required',
            success_url=url_for('success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('cart', _external=True),  # Updated to cart route
        )
        return jsonify(id=checkout_session.id)
    except Exception as e:
        return jsonify(error=str(e)), 403

@app.route('/success')
def success():
    session_id = request.args.get('session_id', None)

    try:
        current_app.logger.info(f"Retrieving session: {session_id}")
        stripe_session = stripe.checkout.Session.retrieve(session_id)
        current_app.logger.info(f"Retrieved session")
        # current_app.logger.info(f"Retrieved session: {stripe_session}")
        
        payment_intent = stripe.PaymentIntent.retrieve(stripe_session.payment_intent)
        current_app.logger.info(f"Retrieved payment_intent")
        # current_app.logger.info(f"Retrieved payment_intent: {payment_intent}")
        
        try:
            if payment_intent.status == 'succeeded':
                cart = session.get('cart', [])

                customer_email = stripe_session.customer_details.email
                customer_name = stripe_session.customer_details.name
                address = stripe_session.customer_details.address
                invoice = stripe_session.id

                send_email(
                    "Your order receipt from AI FLICKS",
                    customer_email, 
                    customer_name, 
                    address, 
                    None,
                    invoice, 
                    payment_intent.amount / 100, 
                    to_customer=True, 
                    cart_items=cart
                )
                current_app.logger.info("Email sent")
                
                # Clear the cart from your app's session
                session.pop('cart', None)
                current_app.logger.info("Cart cleared")

                return render_template('success.html')
            else:
                return redirect(url_for('cart'))
        except Exception as e:
            current_app.logger.error(f"Error: {e}")
            return render_template('fail-checkout.html', error=str(e), token="email")
    except Exception as e:
        current_app.logger.error(f"Error: {e}")
        return render_template('fail-checkout.html', error=str(e), token="checkout")