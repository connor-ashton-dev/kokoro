# syntax=docker/dockerfile:1

########################
# 1️⃣  Base image
########################
FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04 AS runtime

########################
# 2️⃣  Env & OS deps
########################
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_PREFER_BINARY=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

########################
# 3️⃣  Python deps
########################
COPY pyproject.toml uv.lock /tmp/
RUN python -m pip install --upgrade pip uv && \
    uv pip install --system --frozen --no-cache -p /usr/bin/python3.11 --requirement /tmp/pyproject.toml

########################
# 4️⃣  App code
########################
WORKDIR /workspace
COPY handler.py .

########################
# 5️⃣  Entrypoint
########################
CMD ["python", "-u", "handler.py"]
