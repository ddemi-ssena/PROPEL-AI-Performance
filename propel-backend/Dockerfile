# Python 3.10 (stabil Debian tabani)
FROM python:3.10-slim-bookworm

# Çalışma dizini
WORKDIR /app

# Gereksinimleri kopyala ve yükle
COPY requirements.txt .
RUN pip install --default-timeout=1000 --no-cache-dir -r requirements.txt

# Tüm kodu kopyala
COPY . .

EXPOSE 8000

# Environment Path ayarı (Modüllerin bulunabilmesi için)
ENV PYTHONPATH=/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]