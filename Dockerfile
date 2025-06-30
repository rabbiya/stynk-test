# Base image with Python 3.13.2
FROM python:3.13-rc-slim

# Set environment variables to prevent prompts
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies required to build NumPy
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    git \
    libffi-dev \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy all source code into container
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run the application
CMD ["python", "run.py"]

