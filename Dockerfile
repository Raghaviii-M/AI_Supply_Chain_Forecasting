FROM python:3.11-slim

WORKDIR /app

COPY backend /app/backend
COPY requirements.txt /app/

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENV PYTHONPATH=/app/backend

WORKDIR /app/backend

CMD sh -c "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"