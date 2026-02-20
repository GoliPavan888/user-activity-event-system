FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY tests/consumer /app/tests/consumer
COPY pytest.ini /app/pytest.ini

EXPOSE 8001

CMD ["uvicorn", "src.consumer:app", "--host", "0.0.0.0", "--port", "8001"]
