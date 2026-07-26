FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY . .

EXPOSE 5003 8000

CMD ["python", "-m", "windows_listen.listener"]