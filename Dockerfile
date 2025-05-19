FROM python:3.13-slim

# Update & install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy everything from local streamlit_app/ into the container’s /app/
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Streamlit default port
EXPOSE 8501

# Run Streamlit app
CMD ["streamlit", "run", "Main.py", "--server.port=8501", "--server.enableCORS=false"]
