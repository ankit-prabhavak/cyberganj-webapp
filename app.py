from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import face_recognition
import numpy as np
from werkzeug.utils import secure_filename
import base64
from io import BytesIO
from PIL import Image
from scipy.spatial.distance import cosine
import re
from config import Config
from datetime import datetime

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Database setup
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'instance', 'users.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configure image upload folder
app.config['UPLOAD_FOLDER'] = 'static/images/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}


# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    face_encoding = db.Column(db.PickleType, nullable=True)  # Store face encoding
    last_login = db.Column(db.DateTime, nullable=True)  # Store last login timestamp

# Initialize Login Manager
login_manager = LoginManager(app)
login_manager.login_view = "login"  # Redirect to login page if not logged in

# User Loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Custom placeholder filter
@app.template_filter('placeholder')
def placeholder_filter(value):
    """
    Custom Jinja2 filter to handle placeholders.
    Returns the input value if valid, otherwise a default placeholder.
    """
    if value and value != '':
        return value
    if isinstance(value, str) and '2025-05' in value:  # For datetime placeholders
        return datetime.now().strftime('%Y-%m-%d %I:%M %p')
    return 'Not available'

# Context processor for datetime
@app.context_processor
def inject_now():
    return {'now': datetime.now}

# Routes
@app.route('/')
def index():
    """Render the home page."""
    return render_template('index.html')

@app.route('/awareness')
def awareness():
    """Render the cybersecurity awareness articles page."""
    return render_template('awareness.html')

@app.route('/blog')
def blog():
    """Render the blog page."""
    return render_template('blog.html')

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
    """Handle user registration with face encoding."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        Email = request.form['Email']
        phone_number = request.form['phone_number']
        address = request.form['address']
        image_data = request.form['image_data']  # For webcam capture

        if image_data:
            # Convert base64 image data to image
            image_data = image_data.split(',')[1]  # Remove "data:image/png;base64,"
            image_data = base64.b64decode(image_data)
            image = Image.open(BytesIO(image_data))

            # Save image to disk
            filename = secure_filename(f"{username}_profile.png")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(filepath)

            # Process face encoding
            image = face_recognition.load_image_file(filepath)
            face_encoding = face_recognition.face_encodings(image)

            if face_encoding:
                face_encoding = face_encoding[0]  # Get the first face encoding
            else:
                return "No face detected. Please try again with a clearer image."

            # Check if username already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                return "Username already taken. Please choose a different username."

            # Create a new user with the face encoding (convert to list for Pickle)
            new_user = User(
                username=username,
                password=password,
                name=name,
                Email=Email,
                phone_number=phone_number,
                address=address,
                face_encoding=face_encoding.tolist()
            )
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login with credentials or face recognition."""
    if current_user.is_authenticated:
        return redirect(url_for('welcome'))

    if request.method == 'POST':
        if 'username' in request.form and 'password' in request.form:
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()
            if user and user.password == password:
                user.last_login = datetime.now()  # Update last login
                db.session.commit()
                login_user(user)
                next_page = request.form.get('next') or request.args.get('next')
                return redirect(next_page or url_for('welcome'))

        elif 'image_data' in request.form:
            image_data = request.form['image_data']
            if image_data:
                image_data = image_data.split(',')[1]
                image_data = base64.b64decode(image_data)
                image = face_recognition.load_image_file(BytesIO(image_data))
                face_encoding = face_recognition.face_encodings(image)

                if face_encoding:
                    face_encoding = face_encoding[0]
                    users = User.query.all()
                    for u in users:
                        if u.face_encoding is not None:
                            stored_encoding = np.array(u.face_encoding)
                            distance = cosine(stored_encoding, face_encoding)
                            if distance < 0.06:
                                u.last_login = datetime.now()  # Update last login
                                db.session.commit()
                                login_user(u)
                                next_page = request.form.get('next') or request.args.get('next')
                                return redirect(next_page or url_for('welcome'))

                    return "User not registered or face mismatch"

        return "Invalid login method or data."

    return render_template('login.html')

@app.route('/welcome')
@login_required
def welcome():
    """Render the dashboard page."""
    return render_template('welcome.html', user=current_user)

@app.route('/logout')
@login_required
def logout():
    """Handle user logout."""
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
    """API endpoint to check password strength."""
    data = request.get_json()
    password = data.get('password', '')
    
    # Initialize score and feedback
    score = 0
    feedback = []
    
    # Check password length
    if len(password) < 8:
        feedback.append("Password should be at least 8 characters long")
    else:
        score += 1
        
    # Check for uppercase letters
    if not re.search(r'[A-Z]', password):
        feedback.append("Include at least one uppercase letter")
    else:
        score += 1
        
    # Check for lowercase letters
    if not re.search(r'[a-z]', password):
        feedback.append("Include at least one lowercase letter")
    else:
        score += 1
        
    # Check for numbers
    if not re.search(r'\d', password):
        feedback.append("Include at least one number")
    else:
        score += 1
        
    # Check for special characters
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        feedback.append("Include at least one special character")
    else:
        score += 1
    
    # Check for common passwords (simplified)
    common_passwords = ['password', '123456', 'qwerty', 'admin', 'welcome']
    if password.lower() in common_passwords:
        score = 0
        feedback = ["This is a commonly used password and very insecure"]
    
    # Calculate strength category
    strength = ''
    if score == 0:
        strength = 'Very Weak'
    elif score <= 2:
        strength = 'Weak'
    elif score <= 3:
        strength = 'Moderate'
    elif score <= 4:
        strength = 'Strong'
    else:
        strength = 'Very Strong'
    
    return jsonify({
        'score': score,
        'strength': strength,
        'feedback': feedback
    })



# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()  # Create tables
#     app.run(host='0.0.0.0', debug=Config.DEBUG)
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # ✅ Creates all tables on first deployment

    # Do NOT run app.run() here on Render
    # Comment or delete this line after tables are created
    # app.run(host='0.0.0.0', debug=Config.DEBUG)

