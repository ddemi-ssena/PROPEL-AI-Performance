# Python 3.10 kullanıyoruz (ML kütüphaneleri için stabil)
FROM python:3.10-slim

# Çalışma dizini
WORKDIR /app

# Sistem bağımlılıklarını yükle (Postgres derleme araçları gerekebilir)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Gereksinimleri kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Tüm kodu kopyala
COPY . .

EXPOSE 8000

# Environment Path ayarı (Modüllerin bulunabilmesi için)
ENV PYTHONPATH=/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]