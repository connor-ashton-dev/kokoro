# syntax=docker/dockerfile:1

########################
# 1️⃣  Base image
########################
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04 AS runtime

########################
# 2️⃣  Env & OS deps
########################
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_PREFER_BINARY=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3-pip \
    ffmpeg && \
    # Create symlink for python -> python3.11
    ln -s /usr/bin/python3.11 /usr/local/bin/python && \
    rm -rf /var/lib/apt/lists/*

########################
# 3️⃣  Python deps
########################
COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt

########################
# 4️⃣  App code
########################
WORKDIR /workspace
COPY handler.py .

########################
# 5️⃣  Entrypoint
########################
CMD ["python", "-u", "handler.py"]
