FROM python:3.14-slim@sha256:486b8092bfb12997e10d4920897213a06563449c951c5506c2a2cfaf591c599f

WORKDIR /app

# Install pipenv
RUN pip install --no-cache-dir pipenv

# Copy Pipfile and Pipfile.lock and install dependencies
COPY Pipfile Pipfile.lock ./
RUN pipenv install --system --deploy

# Copy application code
COPY app/ ./app/

# Create non-root user and .kube directory for kubeconfig mounting
RUN useradd -m -u 1000 appuser && \
    mkdir -p /home/appuser/.kube && \
    chown -R appuser:appuser /app /home/appuser/.kube
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
