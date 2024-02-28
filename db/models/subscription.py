from .. import db

class Subscription(db.Document):
    meta = {'collection': 'subscriptions'}
    name = db.StringField(max_length=255, required=True, unique=True)
    details = db.DictField(max_length=1000, required=True)