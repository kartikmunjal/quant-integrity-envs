FROM python:3.14-slim@sha256:35caba83af2fe6da9a5d922f9b0156f21d1246a48278c58a08bd253303ba42e8
RUN apt-get update && apt-get install -y --no-install-recommends strace=6.13+ds-1 && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /opt/qi && printf 'Protected E1 runtime harness\n' > /opt/qi/harness && printf 'Synthetic canary, never task input\n' > /opt/qi/canary
WORKDIR /work
