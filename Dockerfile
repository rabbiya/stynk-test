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

