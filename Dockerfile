# Use a slim Python base
FROM python:3.11-slim

# Keep output streaming, useful for logs
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies (adjust if you know you need more/less)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies early to leverage Docker cache
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy the rest of the source
COPY . .

# Ensure upload directory exists (if your app writes to it)
RUN mkdir -p app/uploads && chmod -R a+rw app/uploads

# Expose the port HuggingFace expects (typically 8080)
EXPOSE 8080

# Optional healthcheck (requires curl)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s \
  CMD curl -f http://localhost:8080/ || exit 1

# Entry point: use Gunicorn with Uvicorn worker (works for FastAPI/ASGI apps).
# If you're using Flask (WSGI), you can swap to: ["gunicorn", "main:app", "--bind", "0.0.0.0:8080"]
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8080", "--timeout", "120"]
