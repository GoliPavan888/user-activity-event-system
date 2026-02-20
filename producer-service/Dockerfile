FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src /app/src
COPY ./tests/producer /app/tests/producer
COPY pytest.ini /app/pytest.ini

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
