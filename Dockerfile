# Use official Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (only essentials)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gfortran \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app
COPY . .

# Expose Cloud Run port
EXPOSE 8080

# Run Streamlit
CMD ["streamlit", "run", "streamlit_app_v2.py", "--server.port=8080", "--server.address=0.0.0.0"]
