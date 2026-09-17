FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# Executa o Uvicorn apontando para os certificados SSL
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--ssl-keyfile", "/app/certs/server2.key", "--ssl-certfile", "/app/certs/server2.crt"]