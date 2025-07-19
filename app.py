from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import cv2
import numpy as np
from werkzeug.utils import secure_filename
import base64
from io import BytesIO
from PIL import Image
from scipy.spatial.distance import cosine, euclidean
import re
from config import Config
from datetime import datetime

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Database setup - uses Config settings (PostgreSQL or SQLite)
db = SQLAlchemy(app)

# Configure image upload folder
app.config['UPLOAD_FOLDER'] = 'static/images/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

class FaceRecognizer:
    def __init__(self):
        # Initialize OpenCV face detector and recognizer
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        
    def extract_face_encoding(self, image_path_or_array):
        """Extract face encoding using OpenCV's LBPH feature extraction"""
        try:
            # Load image
            if isinstance(image_path_or_array, str):
                image = cv2.imread(image_path_or_array)
            elif isinstance(image_path_or_array, np.ndarray):
                image = image_path_or_array
            else:
                # Handle PIL Image or BytesIO
                if hasattr(image_path_or_array, 'read'):
                    image_path_or_array.seek(0)
                    image_array = np.frombuffer(image_path_or_array.read(), np.uint8)
                    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                else:
                    image_array = np.array(image_path_or_array)
                    if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                        image = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
                    else:
                        image = image_array
            
            if image is None:
                return None
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            
            if len(faces) == 0:
                return None
            
            # Get the largest face
            face = max(faces, key=lambda rect: rect[2] * rect[3])
            x, y, w, h = face
            
            # Extract face region
            face_gray = gray[y:y+h, x:x+w]
            
            # Resize to standard size for consistency
            face_resized = cv2.resize(face_gray, (100, 100))
            
            # Create a simple feature vector using histogram of oriented gradients
            # and local binary patterns
            features = []
            
            # Divide face into 4x4 grid and calculate LBP histogram for each cell
            cell_h, cell_w = face_resized.shape[0] // 4, face_resized.shape[1] // 4
            
            for i in range(4):
                for j in range(4):
                    cell = face_resized[i*cell_h:(i+1)*cell_h, j*cell_w:(j+1)*cell_w]
                    
                    # Calculate LBP
                    lbp = self._calculate_lbp(cell)
                    
                    # Calculate histogram
                    hist, _ = np.histogram(lbp.ravel(), bins=256, range=[0, 256])
                    features.extend(hist)
            
            # Add some statistical features
            features.extend([
                np.mean(face_resized),
                np.std(face_resized),
                np.median(face_resized),
                np.var(face_resized)
            ])
            
            return np.array(features, dtype=np.float32)
            
        except Exception as e:
            print(f"Error in face encoding extraction: {e}")
            return None
    
    def _calculate_lbp(self, image, radius=1, n_points=8):
        """Calculate Local Binary Pattern"""
        def get_pixel(img, center, x, y):
            new_x = center[0] + x
            new_y = center[1] + y
            if 0 <= new_x < img.shape[0] and 0 <= new_y < img.shape[1]:
                return img[new_x, new_y]
            else:
                return 0
        
        lbp = np.zeros_like(image)
        for i in range(radius, image.shape[0] - radius):
            for j in range(radius, image.shape[1] - radius):
                center = image[i, j]
                code = 0
                for k in range(n_points):
                    angle = 2 * np.pi * k / n_points
                    x = int(radius * np.cos(angle))
                    y = int(radius * np.sin(angle))
                    neighbor = get_pixel(image, (i, j), x, y)
                    if neighbor >= center:
                        code |= (1 << k)
                lbp[i, j] = code
        return lbp
    
    def compare_faces(self, encoding1, encoding2, threshold=0.25):
        """Compare two face encodings using cosine similarity"""
        if encoding1 is None or encoding2 is None:
            return False
        
        try:
            # Ensure both encodings are numpy arrays
            enc1 = np.array(encoding1)
            enc2 = np.array(encoding2)
            
            # Normalize the encodings
            enc1_norm = enc1 / (np.linalg.norm(enc1) + 1e-7)
            enc2_norm = enc2 / (np.linalg.norm(enc2) + 1e-7)
            
            # Calculate cosine similarity (1 - cosine distance)
            cosine_similarity = np.dot(enc1_norm, enc2_norm)
            
            # Convert to distance (lower is better)
            cosine_distance = 1 - cosine_similarity
            
            print(f"Face comparison - Cosine distance: {cosine_distance:.4f}, Threshold: {threshold}")
            
            return cosine_distance < threshold
        except Exception as e:
            print(f"Error in face comparison: {e}")
            return False

# Initialize face recognizer
face_recognizer = FaceRecognizer()

# User model - Updated for PostgreSQL compatibility
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Increased length for PostgreSQL
    name = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(50), nullable=False)
    address = db.Column(db.Text, nullable=False)  # Changed to Text for longer addresses
    face_encoding = db.Column(db.JSON, nullable=True)  # Use JSON instead of PickleType for PostgreSQL
    last_login = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

# Initialize Login Manager
login_manager = LoginManager(app)
login_manager.login_view = "login"

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
    """Custom Jinja2 filter to handle placeholders."""
    if value and value != '':
        return value
    if isinstance(value, str) and '2025-05' in value:
        return datetime.now().strftime('%Y-%m-%d %I:%M %p')
    return 'Not available'

# Context processor for datetime
@app.context_processor
def inject_now():
    return {'now': datetime.now}

# Database initialization route (temporary - remove after first deployment)
@app.route('/init-db')
def init_db():
    """Initialize database tables - Remove this route after first deployment"""
    try:
        db.create_all()
        return "Database tables created successfully!"
    except Exception as e:
        return f"Error creating tables: {str(e)}"

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
        try:
            username = request.form['username']
            password = request.form['password']
            name = request.form['name']
            Email = request.form['Email']
            phone_number = request.form['phone_number']
            address = request.form['address']
            image_data = request.form['image_data']

            if image_data:
                # Convert base64 image data to image
                image_data = image_data.split(',')[1]
                image_data = base64.b64decode(image_data)
                image = Image.open(BytesIO(image_data))

                # Save image to disk
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])
                    
                filename = secure_filename(f"{username}_profile.png")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(filepath)

                # Process face encoding
                face_encoding = face_recognizer.extract_face_encoding(filepath)

                if face_encoding is not None:
                    # Check if username already exists
                    existing_user = User.query.filter_by(username=username).first()
                    if existing_user:
                        return "Username already taken. Please choose a different username."

                    # Create a new user with the face encoding
                    new_user = User(
                        username=username,
                        password=password,
                        name=name,
                        Email=Email,
                        phone_number=phone_number,
                        address=address,
                        face_encoding=face_encoding.tolist() if face_encoding is not None else None
                    )
                    db.session.add(new_user)
                    db.session.commit()

                    return redirect(url_for('login'))
                else:
                    return "No face detected or face processing failed. Please try again with a clearer image."
                    
        except Exception as e:
            print(f"Registration error: {e}")
            db.session.rollback()
            return "Error processing registration. Please try again."

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login with credentials or face recognition."""
    if current_user.is_authenticated:
        return redirect(url_for('welcome'))

    if request.method == 'POST':
        try:
            if 'username' in request.form and 'password' in request.form:
                username = request.form['username']
                password = request.form['password']
                user = User.query.filter_by(username=username).first()
                if user and user.password == password:
                    user.last_login = datetime.now()
                    db.session.commit()
                    login_user(user)
                    next_page = request.form.get('next') or request.args.get('next')
                    return redirect(next_page or url_for('welcome'))

            elif 'image_data' in request.form:
                image_data = request.form['image_data']
                if image_data:
                    # Convert base64 to image data
                    image_data = image_data.split(',')[1]
                    image_data = base64.b64decode(image_data)
                    
                    # Extract face encoding from login image
                    face_encoding = face_recognizer.extract_face_encoding(BytesIO(image_data))

                    if face_encoding is not None:
                        # Compare with all registered users
                        users = User.query.all()
                        best_match = None
                        best_distance = float('inf')
                        
                        for user in users:
                            if user.face_encoding is not None:
                                stored_encoding = np.array(user.face_encoding)
                                
                                # Calculate cosine distance
                                enc1_norm = stored_encoding / (np.linalg.norm(stored_encoding) + 1e-7)
                                enc2_norm = face_encoding / (np.linalg.norm(face_encoding) + 1e-7)
                                cosine_similarity = np.dot(enc1_norm, enc2_norm)
                                distance = 1 - cosine_similarity
                                
                                print(f"User: {user.username}, Distance: {distance:.4f}")
                                
                                if distance < best_distance:
                                    best_distance = distance
                                    best_match = user
                        
                        # Login if best match is below threshold
                        if best_match and best_distance < 0.25:
                            best_match.last_login = datetime.now()
                            db.session.commit()
                            login_user(best_match)
                            next_page = request.form.get('next') or request.args.get('next')
                            print(f"Face login successful for user: {best_match.username} with distance: {best_distance:.4f}")
                            return redirect(next_page or url_for('welcome'))
                        else:
                            if best_match:
                                print(f"Best match {best_match.username} rejected with distance: {best_distance:.4f}")
                            return "Face does not match any registered user or confidence too low."
                    else:
                        return "No face detected in the image. Please try again."
                        
        except Exception as e:
            print(f"Login error: {e}")
            return "Error processing login. Please try again."

        return "Invalid login credentials."

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
    
    # Check for common passwords
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

# Initialize database tables when app starts
with app.app_context():
    try:
        db.create_all()
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error creating tables: {e}")

# For development and production
if __name__ == '__main__':
    # Run on all interfaces for Render deployment
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=Config.DEBUG)