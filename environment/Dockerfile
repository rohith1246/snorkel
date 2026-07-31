# Base Image Justification:
# We use Python 3.13 slim-bookworm pinned by exact digest as mandated by platform rules.
# OpenJDK 17, Maven, Graphviz, Git, tmux, asciinema, gcc, build-essential, and Python packages are installed for Java JWT trust auditing.

FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

ENV TASK_ROOT=/app

# Install OpenJDK 17, Maven, Graphviz, Git, tmux, asciinema, curl, gcc, g++, build-essential
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jdk \
    maven \
    graphviz \
    git \
    tmux \
    asciinema \
    curl \
    gcc \
    g++ \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency manifests first for optimal layer caching
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/requirements.txt

COPY pom.xml /app/pom.xml
COPY key_releases.csv /app/key_releases.csv

# Copy task source files into the image
COPY src /app/src

