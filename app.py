# Sign Language Detector Flask Application
# Hand landmark processing and prediction using Random Forest classifier


from wsgiref.simple_server import WSGIServer
from flask import Flask, jsonify, render_template, url_for, redirect, flash, session, request, Response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from wtforms import StringField, PasswordField, SubmitField
from flask_wtf import FlaskForm
from wtforms.validators import InputRequired, Length, ValidationError, Email, EqualTo
from flask_bcrypt import Bcrypt
from datetime import datetime
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
from flask_mail import Message, Mail
import os
import sys
import random
import re
import pickle
import cv2
import mediapipe as mp
import numpy as np

app = Flask(__name__)
print("Flask app starting - ALL PACKAGES INSTALLED!")  # Debug message

CORS(app)  # Allow cross-origin requests for all routes

# -------------------Encrypt Password using Hash Func-------------------
bcrypt = Bcrypt(app)

# -------------------Database Model Setup-------------------
# Handle database URL for both local and Render environments
database_url = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'thisisasecretkey')
serializer = Serializer(app.config['SECRET_KEY'])
db = SQLAlchemy(app)
app.app_context().push()
print(f"Database configured: {database_url}")  # Debug info


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# -------------------mail configuration-------------------
app.config["MAIL_SERVER"] = 'smtp.gmail.com'
app.config["MAIL_PORT"] = 587
app.config["MAIL_USERNAME"] = os.environ.get('MAIL_USERNAME', 'handssignify@gmail.com')
app.config["MAIL_PASSWORD"] = os.environ.get('MAIL_PASSWORD', 'ttbylakctxvvvnxe')
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False
mail = Mail(app)
# --------------------------------------------------------


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------Database Model-------------------


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False, unique=True)
    email = db.Column(db.String(30), nullable=False)
    password = db.Column(db.String(80), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize database tables
try:
    db.create_all()
    print("Database tables created successfully!")
except Exception as e:
    print(f"Database initialization error: {e}")
# ----------------------------------------------------

# -------------------Health Check Route---------------
@app.route('/health')
def health_check():
    """Health check endpoint for debugging deployment issues"""
    try:
        # Test database connection
        user_count = User.query.count()
        db_status = f"Database OK (users: {user_count})"
    except Exception as e:
        db_status = f"Database Error: {e}"
    
    # Test model status
    model_status = "Model OK" if model is not None else "Model not loaded"
    
    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'model': model_status,
        'python_version': sys.version
    })

# -------------------Welcome or Home Page-------------

@app.route('/', methods=['GET', 'POST'])
def home():
    session.clear()
    return render_template('home.html')
# ----------------------------------------------------

# -------------------feed back Page-----------------------
@app.route('/feed', methods=['GET', 'POST'])
@login_required
def feed():
    return render_template('feed.html')
# ----------------------------------------------------


# -------------------Discover More Page---------------
@app.route('/discover_more', methods=['GET', 'POST']) 
def discover_more():
    return render_template('discover_more.html')
# ----------------------------------------------------

# -------------------Guide Page-----------------------
@app.route('/guide', methods=['GET', 'POST'])
def guide():
    return render_template('guide.html')
# ----------------------------------------------------


# -------------------Login Page-------------------
class LoginForm(FlaskForm):
    username = StringField(label='username', validators=[InputRequired()], render_kw={"placeholder": "Username"})
    email = StringField(label='email', validators=[InputRequired(), Email()], render_kw={"placeholder": "Email"})
    password = PasswordField(label='password', validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    # Check if the user has registered before showing the login form
    if 'registered' in session and session['registered']:
        session.pop('registered', None)
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data) and User.query.filter_by(email=form.email.data).first():
            login_user(user)
            flash('Login successfully.', category='success')
            name = form.username.data
            session['name'] = name
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            flash(f'Login unsuccessful for {form.username.data}.', category='danger')
    return render_template('login.html', form=form)
# ----------------------------------------------------




# -------------------Dashboard or Logged Page-------------------
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if 'logged_in' in session and session['logged_in']:
        name = session.get('name')
        # character = session.get('character')
        # templs = ['detect_characters.html', 'dashboard.html']
        return render_template('dashboard.html', name=name)
    return redirect(url_for('login'))
# ----------------------------------------------------

# -------------------About Page-----------------------
@app.route('/about', methods=['GET', 'POST'])
def about():
    return render_template('about.html')
# ----------------------------------------------------

# -------------------Logged Out Page-------------------

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    session.clear()
    logout_user()
    flash('Account Logged out successfully.', category='success')
    return redirect(url_for('login'))
# ----------------------------------------------------

# -------------------Register Page-------------------

class RegisterForm(FlaskForm):
    username = StringField(label='username', validators=[InputRequired()], render_kw={"placeholder": "Username"})
    email = StringField(label='email', validators=[InputRequired(), Email()], render_kw={"placeholder": "Email"})
    password = PasswordField(label='password', validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    confirm_password = PasswordField(label='confirm_password', validators=[InputRequired(), EqualTo('password')], render_kw={"placeholder": "Confirm Password"})
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            flash('That Username already exists. Please choose a different one.', 'danger')
            raise ValidationError('That username already exists. Please choose a different one.')


@ app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data,email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        # Set a session variable to indicate successful registration
        session['registered'] = True
        flash(f'Account Created for {form.username.data} successfully.', category='success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)
# ----------------------------------------------------

# -------------------Update or reset Email Page-------------------


class ResetMailForm(FlaskForm):
    username = StringField(label='username', validators=[InputRequired()], render_kw={"placeholder": "Username"})
    email = StringField(label='email', validators=[InputRequired(), Email()], render_kw={"placeholder": "Old Email"})
    new_email = StringField(label='new_email', validators=[InputRequired(), Email()], render_kw={"placeholder": "New Email"})
    password = PasswordField(label='password', validators=[InputRequired()], render_kw={"placeholder": "Password"})
    submit = SubmitField('Login', validators=[InputRequired()])


@app.route('/reset_email', methods=['GET', 'POST'])
@login_required
def reset_email():
    form = ResetMailForm()
    if 'logged_in' in session and session['logged_in']:
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and bcrypt.check_password_hash(user.password, form.password.data) and User.query.filter_by(email=form.email.data).first():
                user.email = form.new_email.data  # Replace old email with new email
                db.session.commit()
                flash('Email reset successfully.', category='success')
                session.clear()
                return redirect(url_for('login'))
            else:
                flash('Invalid email, password, or combination.', category='danger')

        return render_template('reset_email.html', form=form)
    return redirect(url_for('login'))
# --------------------------------------------------------------

# -------------------Forgot Password With OTP-------------------

class ResetPasswordForm(FlaskForm):
    username = StringField(label='username', validators=[InputRequired()], render_kw={"placeholder": "Username"})
    email = StringField(label='email', validators=[InputRequired(), Email()], render_kw={"placeholder": "Email"})
    submit = SubmitField('Submit', validators=[InputRequired()])


class ForgotPasswordForm(FlaskForm):
    username = StringField(label='username', validators=[InputRequired()], render_kw={"placeholder": "Username"})
    email = StringField(label='email', validators=[InputRequired(), Email()], render_kw={"placeholder": "Email"})
    new_password = PasswordField(label='new_password', validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "New Password"})
    confirm_password = PasswordField(label='confirm_password', validators=[InputRequired(), EqualTo('new_password')], render_kw={"placeholder": "Confirm Password"})
    otp = StringField(label='otp', validators=[InputRequired(), Length(min=6, max=6)], render_kw={"placeholder": "Enter OTP"})
    submit = SubmitField('Submit', validators=[InputRequired()])


@staticmethod
def send_mail(name, email, otp):
    msg = Message('Reset Email OTP Password',sender='handssignify@gmail.com', recipients=[email])
    msg.body = "Hii " + name + "," + "\nYour email OTP is :"+str(otp)
    mail.send(msg)


    # Generate your OTP logic here
def generate_otp():
    return random.randint(100000, 999999)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    otp = generate_otp()
    session['otp'] = otp
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and User.query.filter_by(email=form.email.data).first():
            send_mail(form.username.data, form.email.data, otp)
            flash('Reset Request Sent. Check your mail.', 'success')
            return redirect(url_for('forgot_password'))
        else:
            flash('Email and username combination is not exist.', 'danger')
    return render_template('reset_password_request.html', form=form)


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        otp = request.form['otp']
        valid = (otp == request.form['otp'])

        if valid:
            user = User.query.filter_by(username=form.username.data).first()
            if user and User.query.filter_by(email=form.email.data).first():
                user.password = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
                db.session.commit()
                flash('Password Changed Successfully.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Email and username combination is not exist.', 'danger')
        else:
            flash("OTP verification failed.", 'danger')
    return render_template('forgot_password.html', form=form)
# ---------------------------------------------------------------

# ------------------------- Update Password ---------------------

class UpdatePasswordForm(FlaskForm):
    username = StringField(label='username', validators=[InputRequired()], render_kw={"placeholder": "Username"})
    email = StringField(label='email', validators=[InputRequired(), Email()], render_kw={"placeholder": "Email"})
    new_password = PasswordField(label='new_password', validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "New Password"})
    confirm_password = PasswordField(label='confirm_password', validators=[InputRequired(), EqualTo('new_password')], render_kw={"placeholder": "Confirm Password"})
    submit = SubmitField('Submit', validators=[InputRequired()])


@app.route('/update_password', methods=['GET', 'POST'])
@login_required
def update_password():
    form = UpdatePasswordForm()
    if form.validate_on_submit() and 'logged_in' in session and session['logged_in']:

            user = User.query.filter_by(username=form.username.data).first()
            if user and User.query.filter_by(email=form.email.data).first():
                user.password = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
                db.session.commit()
                flash('Password Changed Successfully.', 'success')
                session.clear()
                return redirect(url_for('login'))
            else:
                flash("Username and email combination is not exist.", 'danger')
    return render_template('update_password.html', form=form)
# -----------------------------  end  ---------------------------


# --------------------------- Machine Learning ------------------
# Temporarily disabled for deployment without OpenCV/MediaPipe
# --------------------------- Machine Learning ------------------
# Load ML model with better error handling
try:
    model_path = os.path.join(os.path.dirname(__file__), 'model.p')
    if not os.path.exists(model_path):
        model_path = './model.p'  # Fallback to relative path
    
    with open(model_path, 'rb') as f:
        model_dict = pickle.load(f)
    model = model_dict['model']
    print(f"Model loaded successfully from: {model_path}")
except Exception as e:
    print(f"Error loading the model: {e}")
    model = None

# Initialize MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

hands = mp_hands.Hands(static_image_mode=True, min_detection_confidence=0.3)

# Labels for sign language classes
labels_dict = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E', 5: 'F', 6: 'G', 7: 'H', 8: 'I', 9: 'J', 10: 'K', 11: 'L', 12: 'M', 13: 'N', 14: 'O', 15: 'P', 16: 'Q', 17: 'R', 18: 'S', 19: 'T', 20: 'U', 21: 'V', 22: 'W', 23: 'X', 24: 'Y', 25: 'Z'}

def generate_frames():
    """Generate video frames with hand landmark detection"""
    try:
        cap = cv2.VideoCapture(0)
        
        # Check if camera is accessible
        if not cap.isOpened():
            # Create a more informative demo frame
            demo_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Background color
            demo_frame[:] = (40, 40, 40)
            
            # Title
            cv2.putText(demo_frame, 'Sign Language Detector - DEMO', (80, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Main message
            cv2.putText(demo_frame, 'Camera Not Available on Cloud', (120, 120), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            
            # Instructions
            messages = [
                'This is a live demo of the interface',
                'For REAL camera functionality:',
                '1. Download this project locally',
                '2. Install: pip install -r requirements.txt',
                '3. Run: python app.py',
                '4. Your webcam will work perfectly!',
                '',
                f'Model Status: {"✓ Loaded" if model else "✗ Not loaded"}',
                f'Supported Signs: A-Z ({len(labels_dict)} letters)',
                '',
                'Cloud URL: sign-language-gesture-recognition.onrender.com'
            ]
            
            y_pos = 160
            for msg in messages:
                color = (0, 255, 0) if '✓' in msg else (255, 255, 255)
                if '✗' in msg:
                    color = (0, 0, 255)
                cv2.putText(demo_frame, msg, (50, y_pos), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                y_pos += 25
            
            # Simulate hand landmarks for demo
            import time
            current_time = time.time()
            demo_letter = labels_dict[int(current_time) % len(labels_dict)]
            cv2.putText(demo_frame, f'Demo Prediction: {demo_letter}', (200, 430), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            ret, buffer = cv2.imencode('.jpg', demo_frame)
            frame = buffer.tobytes()
            
            while True:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                time.sleep(0.1)  # Update demo every 100ms
            return
        
        while True:
            success, frame = cap.read()
            if not success:
                break
            
            # Convert the frame to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process the frame for hand landmarks
            results = hands.process(rgb_frame)
            
            predicted_character = ''
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw hand landmarks
                    mp_drawing.draw_landmarks(
                        frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                        mp_drawing_styles.get_default_hand_landmarks_style(),
                        mp_drawing_styles.get_default_hand_connections_style()
                    )
                    
                    # Extract landmark data for prediction
                    if model is not None:
                        data_aux = []
                        x_ = []
                        y_ = []
                        
                        for i in range(len(hand_landmarks.landmark)):
                            x = hand_landmarks.landmark[i].x
                            y = hand_landmarks.landmark[i].y
                            x_.append(x)
                            y_.append(y)
                        
                        for i in range(len(hand_landmarks.landmark)):
                            x = hand_landmarks.landmark[i].x
                            y = hand_landmarks.landmark[i].y
                            data_aux.append(x - min(x_))
                            data_aux.append(y - min(y_))
                        
                        # Make prediction
                        try:
                            prediction = model.predict([np.asarray(data_aux)])
                            predicted_character = labels_dict[int(prediction[0])]
                        except Exception as e:
                            print(f"Prediction error: {e}")
                            predicted_character = "?"
            
            # Add predicted character to frame
            if predicted_character:
                cv2.putText(frame, f'Predicted: {predicted_character}', (10, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 0), 3, cv2.LINE_AA)
            
            # Add status text
            cv2.putText(frame, 'Sign Language Detector - Live', (10, frame.shape[0] - 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
            
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            
            # Yield frame in multipart format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
        cap.release()
        
    except Exception as e:
        print(f"Camera initialization error: {e}")
        # Return error frame
        error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(error_frame, f'Camera Error: {str(e)[:40]}', (20, 240), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        cv2.putText(error_frame, 'Camera access may be restricted', (20, 280), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        ret, buffer = cv2.imencode('.jpg', error_frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    try:
        return Response(generate_frames(),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    except Exception as e:
        print(f"Video feed error: {e}")
        return f"Camera error: {e}", 500

@app.route('/camera_info')
def camera_info():
    """Provide information about camera functionality"""
    return jsonify({
        "camera_available": False,
        "message": "Camera access is restricted on cloud deployments",
        "suggestion": "Download and run locally for full camera functionality",
        "model_loaded": model is not None,
        "supported_signs": list(labels_dict.values()) if model else [],
        "github_repo": "https://github.com/kalyanakash/Sign-Language-Gesture-Recognition",
        "setup_instructions": [
            "1. Clone: git clone https://github.com/kalyanakash/Sign-Language-Gesture-Recognition.git",
            "2. Install: pip install -r requirements.txt", 
            "3. Run: python app.py",
            "4. Open: http://localhost:5000",
            "5. Enable your webcam and enjoy real-time sign language detection!"
        ]
    })

@app.route('/local_setup')
def local_setup():
    """Display local setup instructions"""
    return render_template('setup_guide.html' if os.path.exists('templates/setup_guide.html') else 'guide.html')

@app.route('/download_instructions')
def download_instructions():
    """Provide download and setup instructions"""
    instructions = {
        "title": "Get Full Camera Functionality",
        "description": "Download and run this project locally to use your webcam for real-time sign language detection",
        "steps": [
            {
                "step": 1,
                "title": "Download the Project",
                "description": "Clone or download from GitHub",
                "command": "git clone https://github.com/kalyanakash/Sign-Language-Gesture-Recognition.git"
            },
            {
                "step": 2, 
                "title": "Install Dependencies",
                "description": "Install all required packages",
                "command": "pip install -r requirements.txt"
            },
            {
                "step": 3,
                "title": "Run Locally",
                "description": "Start the application",
                "command": "python app.py"
            },
            {
                "step": 4,
                "title": "Access Locally",
                "description": "Open in your browser",
                "command": "http://localhost:5000"
            }
        ],
        "features": [
            "Real-time webcam access",
            "Live hand landmark detection", 
            "Instant sign language recognition",
            "All 26 ASL letters (A-Z)",
            "No cloud limitations"
        ]
    }
    return jsonify(instructions)

@app.route('/generate_frames', methods=['POST'])
def generate_frames_api():
    """API endpoint for frame generation (legacy support)"""
    return jsonify({"status": "Camera functionality moved to /video_feed"})

# -----------------------------  end  ---------------------------

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
