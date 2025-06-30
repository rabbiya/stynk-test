# Base image with Python 3.13.2
FROM python:3.13-rc-slim

# Set working directory
WORKDIR /app

# Copy dependencies
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy all source code into container
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run the application using python run.py
CMD ["python", "run.py"]
