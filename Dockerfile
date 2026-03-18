FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
WORKDIR /app/game_server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]