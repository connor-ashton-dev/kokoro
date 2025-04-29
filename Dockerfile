# syntax=docker/dockerfile:1

########################
# 1️⃣  Base image
########################
# • The runpod/pytorch images already include CUDA, cuDNN, NCCL and PyTorch
#   built with GPU support – exactly what Serverless needs. :contentReference[oaicite:0]{index=0}
# • Pick the smallest *runtime* flavour that still has Python.
ARG PY_VERSION=3.11
ARG TORCH_VERSION=2.2.2
FROM runpod/pytorch:${TORCH_VERSION}-py${PY_VERSION}-cu121-runtime-ubuntu22.04 AS runtime

########################
# 2️⃣  Env + OS deps
########################
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_PREFER_BINARY=1

# only the libs Kokoro really needs
RUN apt-get update && \
    apt-get install -y --no-install-recommends libsndfile1 ffmpeg && \
    rm -rf /var/lib/apt/lists/*

########################
# 3️⃣  Python deps
########################
# Pin versions for repeatability; copy in early for layer-cache wins.
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
