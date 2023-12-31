from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_session import Session
from flask_login import LoginManager, current_user
from flask_mongoengine import MongoEngine
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.mongoengine import ModelView
from config.config import Config
from dotenv import load_dotenv

load_dotenv()

db = MongoEngine()
login_manager = LoginManager()

class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_admin: # replace has_role with is_admin
            return abort(403)
        return redirect(url_for('aiflix.admin_dashboard'))

def create_app(config_class=Config):
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(config_class)

    Session(app)
    db.init_app(app)
    login_manager.init_app(app)

    from . import models
    admin = Admin(app, name='Dashboard', template_mode='bootstrap3', index_view=MyAdminIndexView())
    admin.add_view(ModelView(models.User))

    from .views import main_bp, admin_bp, auth_bp, user_bp, gallery_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(gallery_bp)
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @login_manager.user_loader
    def load_user(user_id):
        return models.User.objects(pk=user_id).first()

    @login_manager.unauthorized_handler
    def unauthorized():
        flash('You must be logged in to view this page.')
        return redirect(url_for('auth.login'))

    return app