FROM python:3.9-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    chromium nodejs \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -ms /bin/bash app
WORKDIR /app

COPY ./src /app

RUN chown -R app:app /app && \
    chmod -R 555 /app && \
    mkdir -p /app/instance && \
    chown -R app:app /app/instance && \
    mkdir -p /app/uploads && \
    chown -R app:app /app/uploads
    
USER app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]