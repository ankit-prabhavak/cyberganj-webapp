from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import numpy as np
import cv2
from werkzeug.utils import secure_filename
import base64
from io import BytesIO
from PIL import Image
import re
from config import Config
from datetime import datetime
import pickle

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Database setup
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'instance', 'users.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/images/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

db = SQLAlchemy(app)

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    image_path = db.Column(db.String(200), nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)

login_manager = LoginManager(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.template_filter('placeholder')
def placeholder_filter(value):
    if value and value != '':
        return value
    if isinstance(value, str) and '2025-05' in value:
        return datetime.now().strftime('%Y-%m-%d %I:%M %p')
    return 'Not available'

@app.context_processor
def inject_now():
    return {'now': datetime.now}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/awareness')
def awareness():
    """Render the cybersecurity awareness articles page."""
    return render_template('awareness.html')

@app.route('/terms')
def terms():
    """Render the terms and conditions page."""
    return "Terms and conditions page (To be implemented)"

@app.route('/privacy')
def privacy():
    """Render the privacy policy page."""
    return "Privacy Policy page (To be implemented)"

@app.route('/phishing_attacks')
def phishing_attacks():
    """Render the phishing page."""
    return render_template('phishing_attacks.html')

@app.route('/malware')
def malware():
    """Render the malware page."""
    return render_template('malware.html')

@app.route('/password')
def password():
    """Render the password security page."""
    return render_template('password.html')

@app.route('/tools')
def tools():
    """Render the interactive tools page."""
    return render_template('tools.html')

@app.route('/resources')
@login_required
def resources():
    """Render the resources page."""
    return render_template('resources.html', user=current_user)

@app.route('/about')
def about():
    """Render the about page."""
    return render_template('about.html')

@app.route('/home')
def home():
    """Render the home page for account creation."""
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        Email = request.form['Email']
        phone_number = request.form['phone_number']
        address = request.form['address']
        image_data = request.form['image_data']

        if image_data:
            image_data = image_data.split(',')[1]
            image_data = base64.b64decode(image_data)
            image = Image.open(BytesIO(image_data)).convert('L')
            filename = secure_filename(f"{username}_profile.png")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(filepath)

            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                return "Username already exists"

            new_user = User(
                username=username,
                password=password,
                name=name,
                Email=Email,
                phone_number=phone_number,
                address=address,
                image_path=filepath
            )
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('welcome'))

    if request.method == 'POST':
        if 'username' in request.form and 'password' in request.form:
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()
            if user and user.password == password:
                user.last_login = datetime.now()
                db.session.commit()
                login_user(user)
                return redirect(url_for('welcome'))

        elif 'image_data' in request.form:
            image_data = request.form['image_data']
            image_data = image_data.split(',')[1]
            image_data = base64.b64decode(image_data)
            image = Image.open(BytesIO(image_data)).convert('L')
            image_np = np.array(image)

            users = User.query.all()
            for u in users:
                if u.image_path and os.path.exists(u.image_path):
                    stored_image = cv2.imread(u.image_path, cv2.IMREAD_GRAYSCALE)
                    recognizer = cv2.face.LBPHFaceRecognizer_create()
                    recognizer.train([stored_image], np.array([u.id]))
                    label, confidence = recognizer.predict(image_np)
                    if label == u.id and confidence > 65:
                        u.last_login = datetime.now()
                        db.session.commit()
                        login_user(u)
                        return redirect(url_for('welcome'))

            return "Face not recognized"

    return render_template('login.html')

@app.route('/welcome')
@login_required
def welcome():
    return render_template('welcome.html', user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return render_template('logout.html')

@app.route('/update_profile')
@login_required
def update_profile():
    """Placeholder route for updating user profile."""
    return "Update Profile page (To be implemented)"

@app.route('/security_check')
@login_required
def security_check():
    """Placeholder route for checking security status."""
    return "Security Check page (To be implemented)"


@app.route('/api/check-password', methods=['POST'])
def check_password():
    data = request.get_json()
    password = data.get('password', '')
    score = 0
    feedback = []

    if len(password) < 8:
        feedback.append("Password should be at least 8 characters long")
    else:
        score += 1

    if not re.search(r'[A-Z]', password):
        feedback.append("Include at least one uppercase letter")
    else:
        score += 1

    if not re.search(r'[a-z]', password):
        feedback.append("Include at least one lowercase letter")
    else:
        score += 1

    if not re.search(r'\d', password):
        feedback.append("Include at least one number")
    else:
        score += 1

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        feedback.append("Include at least one special character")
    else:
        score += 1

    if password.lower() in ['password', '123456', 'qwerty', 'admin', 'welcome']:
        score = 0
        feedback = ["This is a commonly used password and very insecure"]

    strength = ['Very Weak', 'Weak', 'Moderate', 'Strong', 'Very Strong'][min(score, 4)]

    return jsonify({
        'score': score,
        'strength': strength,
        'feedback': feedback
    })

@app.before_first_request
def create_tables():
    db.create_all()


# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()
    # app.run(debug=Config.DEBUG) 
