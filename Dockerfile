FROM python:3.12-slim
WORKDIR /app
COPY . /app
ENV PYTHONUNBUFFERED=1
EXPOSE 5000
CMD ["python", "server_v32.py"]
