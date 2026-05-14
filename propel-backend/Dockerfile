# Python 3.10 (stabil Debian tabani)
FROM python:3.10-slim-bookworm

# LightGBM ve XGBoost icin system kutuphaneleri
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Çalışma dizini
WORKDIR /app

# Gereksinimleri kopyala ve yükle
COPY requirements.txt requirements-nlp.txt ./
ARG INSTALL_NLP_DEPS=false
RUN pip install --default-timeout=1000 --no-cache-dir -r requirements.txt \
    && if [ "$INSTALL_NLP_DEPS" = "true" ]; then pip install --default-timeout=1000 --no-cache-dir -r requirements-nlp.txt; fi
COPY requirements.txt .
RUN pip install --default-timeout=1000 --no-cache-dir -r requirements.txt

# Tüm kodu kopyala
COPY . .

EXPOSE 8000

# Environment Path ayarı (Modüllerin bulunabilmesi için)
ENV PYTHONPATH=/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
