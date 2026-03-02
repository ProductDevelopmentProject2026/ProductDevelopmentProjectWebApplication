FROM python:3.12-alpine3.20

RUN apk add --no-cache \
    build-base \
    libpq-dev \
    musl-dev \
    libxml2-dev \
    libxslt-dev

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=core.settings

EXPOSE 8080

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT [ "/app/entrypoint.sh" ]

#CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8080"]