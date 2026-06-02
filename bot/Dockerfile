FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/backend

RUN apt-get update && apt-get install -y --no-install-recommends fonts-dejavu-core && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend-requirements.txt
COPY bot/requirements.txt /app/bot-requirements.txt
RUN pip install --no-cache-dir -r /app/backend-requirements.txt -r /app/bot-requirements.txt

COPY backend /app/backend
COPY bot /app/bot

CMD ["python", "-m", "bot.main"]
