# Dockerfile
FROM python:3.9.17-bookworm

ENV PYTHONUNBUFFERED True

ENV APP_HOME /back-end
WORKDIR $APP_HOME
COPY . .

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 index:app