FROM python:3.14.7

RUN apt-get update && \
      apt-get install -y --no-install-recommends postgresql-client libpq-dev build-essential netcat-openbsd && \
      rm -rf /var/lib/apt/lists/*
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

ENV PATH="/scripts:$PATH"

COPY docker/backend/requirements.txt /requirements.txt
COPY ./backend /backend
COPY docker/backend/scripts /scripts
RUN chmod +x /scripts/*

WORKDIR /backend


RUN pip install -r /requirements.txt

ENTRYPOINT ["/scripts/entrypoint.sh"]
CMD ["/scripts/start_dev_server.sh"]
