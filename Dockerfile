FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

# Create and use virtual environment to avoid pip root warning
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY src ./src

# Expose the port NiceGUI runs on
EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Run the consolidated app
CMD ["python", "-m", "src.main"]
