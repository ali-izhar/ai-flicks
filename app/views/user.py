import os
from flask import render_template, redirect, url_for, session, jsonify, Blueprint
from flask_login import login_required, current_user
from app.services import create_subscription
from app.data import PLANS, PLAN_PRICES
import stripe

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

user_bp = Blueprint('aiflix_user', __name__, url_prefix='/aiflix_user')

@user_bp.route('/create_checkout_session/<plan_name>', methods=['GET', 'POST'])
@login_required
def create_checkout_session(plan_name):
    session['plan_name'] = plan_name

    if plan_name not in PLAN_PRICES:
        return jsonify(error='Invalid plan selected'), 400

    try:
        product = stripe.Product.create(name=plan_name)
        
        price = stripe.Price.create(
          product=product.id,
          unit_amount=PLAN_PRICES[plan_name] * 100,
          currency='usd',
          recurring={"interval": "month"},
        )

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price.id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=url_for('aiflix_user.subscription_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('aiflix_user.subscription_failed', _external=True),
        )

        session['plan_name'] = plan_name
        return redirect(checkout_session.url, code=303)

    except Exception as e:
        return jsonify(error=str(e)), 403

@user_bp.route('/upgrade_subscription/<new_subscription_name>', methods=['GET', 'POST'])
@login_required
def upgrade_subscription(new_subscription_name):
    user = current_user
    create_subscription(new_subscription_name, PLANS[new_subscription_name])
    user.upgrade_subscription(new_subscription_name)
    return redirect(url_for('auth.login'))

@user_bp.route('/downgrade_subscription/<new_subscription_name>', methods=['GET', 'POST'])
@login_required
def downgrade_subscription(new_subscription_name):
    user = current_user
    create_subscription(new_subscription_name, PLANS[new_subscription_name])
    user.downgrade_subscription(new_subscription_name)
    return redirect(url_for('auth.login'))

@user_bp.route('/subscription_success')
def subscription_success():
    user = current_user
    selected_plan = session.get('plan_name')

    if selected_plan:
        new_subscription = create_subscription(selected_plan, PLANS[selected_plan])
        user.subscription = new_subscription
        user.save()
        session.pop('plan_name', None)
    return render_template('payment_success.html')

@user_bp.route('/subscription_failed')
def subscription_failed():
    return render_template('payment_failed.html')