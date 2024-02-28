import base64
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from .. import db
from .subscription import Subscription


class User(UserMixin, db.Document):
    meta = {'collection': 'users'}
    email = db.StringField(max_length=255, required=True, unique=True)
    password = db.StringField(required=True)
    since = db.DateTimeField(default=datetime.utcnow)
    avatar = db.BinaryField()
    subscription = db.ReferenceField('Subscription', default=Subscription.objects(name="Free").first())
    is_admin = db.BooleanField(default=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def set_avatar(self, avatar):
        self.avatar = avatar
        self.save()

    def get_avatar(self):
        if self.avatar is not None:
            avatar_base64 = base64.b64encode(self.avatar).decode('utf-8')
            return f"data:image/png;base64,{avatar_base64}"
        else:
            return None
    
    def get_subscription(self):
        return self.subscription

    def upgrade_subscription(self, subscription_name):
        new_subscription = Subscription.objects(name=subscription_name).first()
        if new_subscription:
            self.subscription = new_subscription
            self.save()

    def downgrade_subscription(self, subscription_name):
        new_subscription = Subscription.objects(name=subscription_name).first()
        if new_subscription:
            self.subscription = new_subscription
            self.save()