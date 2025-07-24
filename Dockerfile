# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create instance directory
RUN mkdir -p instance

# Expose port
EXPOSE $PORT

# Run the application
CMD gunicorn --bind 0.0.0.0:$PORT app:app
