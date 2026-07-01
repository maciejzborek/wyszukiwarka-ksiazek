FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (layer caching)
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ .

EXPOSE 8000

ENV APP_VERSION=1.0.1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
