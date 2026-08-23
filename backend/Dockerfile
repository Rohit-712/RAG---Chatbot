# RAG Chatbot Backend
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# System packages required by common Python/FAISS dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY app ./app

# Runtime directories
RUN mkdir -p /app/uploads /app/data /app/vector_store

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
