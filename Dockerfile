# ============================================================================
# PLAGIA ENTERPRISE - DOCKERFILE MULTI-ETAPA (UV + PYTHON 3.12 + CUDA)
# Optimizado para ejecucion sobre WSL 2 con NVIDIA Container Toolkit
# ============================================================================
FROM nvidia/cuda:12.6.2-cudnn-runtime-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

# Dependencias del sistema para OpenCV, Rasterio (GDAL) y PostGIS
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    libgl1 \
    libglib2.0-0 \
    libgdal-dev \
    gdal-bin \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar binario oficial de uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Instalar Python 3.12 y dependencias cacheadas con uv
COPY .python-version pyproject.toml ./
RUN uv python install 3.12 && \
    uv sync --python 3.12 --no-install-project

# Copiar el codigo fuente empresarial
COPY engine ./engine
COPY backend ./backend
COPY scripts ./scripts
COPY README.md ./

RUN uv sync --python 3.12

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
