FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHON_VERSION=3.10.14

RUN apt-get update && apt-get install -y \
  make build-essential libssl-dev zlib1g-dev \
  libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
  libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
  libffi-dev liblzma-dev git ca-certificates python3-venv \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN python3 -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
