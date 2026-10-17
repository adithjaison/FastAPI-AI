FROM rabbitmq:4.0-management

RUN apt-get update && \
  apt-get install -y --no-install-recommends netcat-openbsd && \
  rm -rf /var/lib/apt/lists/*

COPY scripts/wait-for /bin/wait-for
RUN chmod +x /bin/wait-for

ENV PATH="/bin:$PATH"

