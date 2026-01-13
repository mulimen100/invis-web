# Base Image: Official Python 3.10 Slim
FROM python:3.10-slim

# Set Working Directory
WORKDIR /app

# Install Dependencies
# We copy strict requirements first to leverage caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Project Code
# Note: .dockerignore handles exclusions (node_modules, logs, state)
COPY . .

# Ensure storage directories exist
RUN mkdir -p /app/state /app/logs /app/orders

# Single Entrypoint
ENTRYPOINT ["python", "main.py"]
