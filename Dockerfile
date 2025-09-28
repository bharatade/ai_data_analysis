# Use Python 3.10 to avoid pandasai/pandas build issues
FROM python:3.10-slim

# OS deps needed for wheels / pandas and general builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working dir
WORKDIR /streamlit_app_v2.py

# Copy requirements first for better caching
COPY requirements.txt .

# Install pip and dependencies
RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Streamlit runs on $PORT (Cloud Run). Expose 8080 (Cloud Run default)
ENV PORT=8080
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_PORT=$PORT
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Run Streamlit
CMD ["streamlit", "run", "streamlit_app_v2.py", "--server.port", "8080", "--server.address", "0.0.0.0"]
