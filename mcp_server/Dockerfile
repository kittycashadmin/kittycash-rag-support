# © 2025 Kittycash Team. All rights reserved to Trustnet Systems LLP.

FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 9000 9001
CMD ["python", "server.py", "--host", "0.0.0.0", "--port", "9000", "--meta-port", "9001"]
