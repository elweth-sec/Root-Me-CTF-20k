FROM python:3.9-slim

RUN useradd -ms /bin/bash app
WORKDIR /app

COPY ./src /app

RUN chown -R app:app /app && \
    chmod -R 555 /app && \
    mkdir -p /app/instance && \
    chown -R app:app /app/instance

USER app
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]