FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

# Create and use virtual environment to avoid pip root warning
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Healthcheck using native Python (urllib)
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#     CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/health').getcode() == 200 else 1)"
# COPY src ./src

# Expose the port NiceGUI runs on
EXPOSE 8080


# Run the consolidated app
CMD ["python", "-m", "src.main"]
