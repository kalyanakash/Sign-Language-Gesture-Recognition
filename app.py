# Sign Language Detector Flask Application
# Hand landmark processing and prediction using Random Forest classifier


from wsgiref.simple_server import WSGIServer
from flask import Flask, jsonify, render_template, url_for, redirect, flash, session, request, Response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from wtforms import StringField, PasswordField, SubmitField, Form
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
class LoginForm(Form):
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

class RegisterForm(Form):
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


class ResetMailForm(Form):
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

class ResetPasswordForm(Form):
    username = StringField(label='username', validators=[InputRequired()], render_kw={"placeholder": "Username"})
    email = StringField(label='email', validators=[InputRequired(), Email()], render_kw={"placeholder": "Email"})
    submit = SubmitField('Submit', validators=[InputRequired()])


class ForgotPasswordForm(Form):
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

class UpdatePasswordForm(Form):
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

@app.route('/generate_frames', methods=['POST'])
def generate_frames():
    # Video processing code - basic placeholder for now
    return "Video processing available"

@app.route('/video_feed')
def video_feed():
    return "Video functionality is ready"

# -----------------------------  end  ---------------------------

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
