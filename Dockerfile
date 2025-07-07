FROM python:3.13.3-slim

# Prevents writing .pyc files and ensures logs appear immediately
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install build tools, Rust (for tiktoken), and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    curl \
    gcc \
    pkg-config \
    git \
    && curl https://sh.rustup.rs -sSf | bash -s -- -y \
    && export PATH="/root/.cargo/bin:$PATH" \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.cargo/bin:$PATH"

# Copy dependency list
COPY requirements.txt .

# Install Python packages
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy app code
COPY . .

# Expose API port
EXPOSE 8000

# Start the FastAPI app
CMD ["python", "run.py"]

