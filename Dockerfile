# ---- Base image ----
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Prevent Python from writing .pyc files & buffer stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install dependencies first (layer caching)
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app/ .

# Create a non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Ensure app files are readable/owned by the non-root user
# (guards against restrictive permissions from some host filesystems/mounts)
RUN chown -R appuser:appgroup /app && chmod -R u+rX /app

USER appuser

EXPOSE 5000

# Basic container health check
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Run with gunicorn in production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
