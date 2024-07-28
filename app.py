from flask import Flask, render_template, redirect, url_for, session, request
from flask_login import LoginManager
from models import db, Admin, User
from auth import auth_bp
from admin import admin_bp


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'your_secret_key'

# Initialize Flask extensions with the app
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

# Register the Blueprint
app.register_blueprint(auth_bp, url_prefix='/')
# Register the Blueprint with a URL prefix
app.register_blueprint(admin_bp, url_prefix='/admin')  


@login_manager.user_loader
def load_user(user_id):
    if user_id.startswith('user_'):
        user_id = user_id.replace('user_', '')
        return User.query.get(int(user_id))
    elif user_id.startswith('admin_'):
        admin_id = user_id.replace('admin_', '')
        return Admin.query.get(int(admin_id))
    return None

@login_manager.unauthorized_handler
def unauthorized_callback():
    # Check the URL the user is trying to access
    if request.path.startswith('/admin/dashboard'):
        return redirect(url_for('admin.admin_login'))
    else:
        return redirect(url_for('auth.login'))

def create_tables():
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Tables created successfully.")
        
@app.before_request
def set_default_language():
    # Set default language to 'fr' if not already set
    if 'language' not in session:
        session['language'] = 'fr'

@app.route('/')
def home():
    return render_template('landing.html')

@app.route('/login/<language>', methods=['GET'])
def select_language(language):
    session['language'] = language
    print(session["language"])
    return redirect(url_for("auth.login"))


if __name__ == '__main__':
    # Delete existing database file
    import os
    if os.path.exists('database.db'):
        os.remove('database.db')
    
    create_tables()  # Ensure tables are created before running the app
    app.run(debug=True)
