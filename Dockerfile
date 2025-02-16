FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get clean && apt-get update && apt-get install -y \
    curl \
    python3-tk \
    xvfb \
    libx11-6 \
    libxext6 \
    python3-magic \
    libmagic1 \
    tesseract-ocr \
    libtesseract-dev \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files first for better caching
COPY requirements*.txt ./
COPY base-requirements.txt ./

# Install Python dependencies in a single layer
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-core.txt \
    && pip install --no-cache-dir -r base-requirements.txt

# Copy source code
COPY src/ ./src/
COPY config/ ./config/

# Set environment variables
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    DISPLAY=:99

# Expose ports
EXPOSE 8080

# Run the application with Xvfb
CMD ["uvicorn", "services.service_registry:app", "--host", "0.0.0.0", "--port", "8080"]