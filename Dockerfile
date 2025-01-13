FROM python:3.10

ARG POSTGRES_USER
ARG POSTGRES_PASSWORD
ARG POSTGRES_DB
ARG DATABASE_URL

WORKDIR /app

RUN apt-get update && apt-get install -y cron postgresql-client tzdata && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock ./
RUN pip install -U poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-root --no-interaction --no-ansi

COPY . .

RUN chmod +x /app/main.py

COPY cronjobs /etc/cron.d/cronjobs
RUN chmod 0644 /etc/cron.d/cronjobs
RUN touch /var/log/cron.log

ENV POSTGRES_USER=${POSTGRES_USER}
ENV POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
ENV POSTGRES_DB=${POSTGRES_DB}
ENV DATABASE_URL=${DATABASE_URL}

#CMD ["bash", "-c", "cron && tail -f /var/log/cron.log"]
CMD ["cron", "-f"]