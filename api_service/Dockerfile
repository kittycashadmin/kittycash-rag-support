# © 2025 Kittycash Team. All rights reserved to Trustnet Systems LLP.

FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 9006

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9006", "--reload"]
