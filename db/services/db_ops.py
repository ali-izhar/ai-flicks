from ..models import User, Subscription

def create_user(email, password, avatar):
    user = User(email=email)
    user.set_password(password)
    user.set_avatar(avatar)
    user.save()
    return user

def get_all_users():
    return User.objects()

def get_user_by_email(email):
    return User.objects(email=email).first()

def get_users_by_subscription(subscription_name):
    return User.objects(subscription__name=subscription_name)

def create_subscription(name, details):
    subscription = Subscription(name=name, details=details)
    subscription.save()
    return subscription

def get_plan_by_name(plan_name):
    return Subscription.objects(name=plan_name).first()