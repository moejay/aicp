FROM python:3.10

WORKDIR /app

COPY requirements/aicp-backend.requirements.txt /app/requirements.txt

RUN pip install -r requirements.txt --no-cache-dir --upgrade

COPY backend /app

CMD ["uvicorn", "backend.asgi:application", "--host", "0.0.0.0", "--port", "80"]
