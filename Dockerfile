FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for some ML libraries
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure directories exist
RUN mkdir -p models results

# Default command to run the pipeline
# We use small number of epochs by default for quick validation in Docker
CMD ["python", "pipeline.py", "--epochs", "5"]
