# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV and MediaPipe
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libfontconfig1 \
    libxrender1 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first
RUN pip install --upgrade pip

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies one by one to catch errors
RUN pip install --no-cache-dir Flask==3.0.2
RUN pip install --no-cache-dir gunicorn==21.2.0
RUN pip install --no-cache-dir flask-cors==4.0.0
RUN pip install --no-cache-dir flask-sqlalchemy==3.0.5
RUN pip install --no-cache-dir flask-login==0.6.3
RUN pip install --no-cache-dir flask-wtf==1.1.1
RUN pip install --no-cache-dir flask-bcrypt==1.0.1
RUN pip install --no-cache-dir flask-mail==0.9.1
RUN pip install --no-cache-dir itsdangerous==2.1.2
RUN pip install --no-cache-dir WTForms==3.0.1
RUN pip install --no-cache-dir numpy==1.24.3
RUN pip install --no-cache-dir scikit-learn==1.3.0
RUN pip install --no-cache-dir opencv-python-headless==4.8.0.74
RUN pip install --no-cache-dir mediapipe==0.10.2

# Copy application code
COPY . .

# Create instance directory for SQLite database
RUN mkdir -p instance

# Expose port
EXPOSE $PORT

# Run the application
CMD gunicorn --bind 0.0.0.0:$PORT app:app
