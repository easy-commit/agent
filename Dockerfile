FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHON_VERSION=3.10.14

RUN apt-get update && apt-get install -y \
  make build-essential libssl-dev zlib1g-dev \
  libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
  libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
  libffi-dev liblzma-dev git ca-certificates \
  && rm -rf /var/lib/apt/lists/*

ENV PYENV_ROOT="/root/.pyenv"
ENV PATH="$PYENV_ROOT/bin:$PATH"
RUN curl https://pyenv.run | bash

RUN bash -c "source ~/.bashrc && \
  pyenv install --skip-existing $PYTHON_VERSION && \
  pyenv global $PYTHON_VERSION"

ENV PATH="/root/.pyenv/versions/$PYTHON_VERSION/bin:$PATH"

WORKDIR /app

COPY . .

RUN python -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

CMD if [ "$TRAIN_ON_START" = "true" ]; then \
      echo "🏋️  Training on container start..." && python train_model.py; \
    fi && \
    echo "🌍  Starting server..." && gunicorn server:app --bind 0.0.0.0:5000 --workers 4 --threads 2
