FROM python:3.11-slim

WORKDIR /app

# Copy requirements first (Docker cache optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server.py .

# ❌ Do NOT hardcode PORT
# Cloud Run will inject PORT automatically

# Start the server
CMD ["python", "server.py"]
