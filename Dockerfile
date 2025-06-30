<<<<<<< HEAD
FROM python:3.13.2-slim

WORKDIR /app

# ---- system build deps ----
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential        \
        gfortran               \
        git                    \
        && rm -rf /var/lib/apt/lists/*

# ---- python deps ----
# First install critical pins to avoid earlier errors
RUN pip install --upgrade pip && \
    pip install \
        "pydantic>=1.10.14,<2.0" \
        "langgraph>=0.0.33"

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python", "run.py"]

=======
# Use official Python 3.13.2 base image
FROM python:3.13.2-slim

# Set working directory
WORKDIR /app

# Install required OS packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        g++ \
        git \
        curl \
        wget \
        unzip \
        libffi-dev \
        libssl-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency list
COPY requirements.txt .

# Upgrade pip and install pinned core dependencies first to avoid resolution issues
RUN pip install --upgrade pip && \
    pip install --prefer-binary --no-cache-dir \
        "anyio>=3.6,<4.0" \
        "pydantic>=1.10.14,<2.0" \
        "langgraph>=0.0.33"

# Then install remaining dependencies
RUN pip install --prefer-binary --no-cache-dir -r requirements.txt

# Copy rest of the application
COPY . .

# Expose the port FastAPI runs on
EXPOSE 8000

# Default command to run the app
CMD ["python", "run.py"]
>>>>>>> 38e22a6842795409763f4c510e8078b489df5111
