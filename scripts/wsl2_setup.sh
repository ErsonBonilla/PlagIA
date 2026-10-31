#!/usr/bin/env bash
# ============================================================================
# PLAGIA ENTERPRISE - APROVISIONAMIENTO WSL 2 (UBUNTU + UV + PYTHON 3.12 + CUDA)
# Optimizado para NVIDIA GeForce RTX 3050 (4 GB VRAM, Ampere)
# ============================================================================
set -euo pipefail

echo "============================================================================"
echo " PlagIA Enterprise - Configuracion de Entorno en WSL 2 (Ubuntu)"
echo "============================================================================"

# 1. Verificar acceso al driver NVIDIA de Windows expuesto en WSL 2
if [ -e /usr/lib/wsl/lib/nvidia-smi ]; then
    echo "[OK] Driver NVIDIA WSL 2 detectado:"
    /usr/lib/wsl/lib/nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
elif command -v nvidia-smi >/dev/null 2>&1; then
    echo "[OK] nvidia-smi detectado:"
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
else
    echo "[WARN] No se detecto /usr/lib/wsl/lib/nvidia-smi. Verifica el driver NVIDIA en Windows."
fi

# 2. Instalar librerias nativas ligeras para OpenCV y GDAL/Rasterio
echo "[1/4] Verificando dependencias del sistema para Geoprocesamiento y Vision..."
sudo apt-get update -y
sudo apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    libgl1 \
    libglib2.0-0 \
    libgdal-dev \
    gdal-bin

# 3. Verificar o instalar uv
echo "[2/4] Verificando gestor de paquetes uv..."
if ! command -v uv >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi
uv --version

# 4. Sincronizar Python 3.12 y paquetes con soporte CUDA
echo "[3/4] Sincronizando entorno Python 3.12 con uv (indice PyTorch CUDA cu126)..."
uv python install 3.12
uv sync --python 3.12

# 5. Ejecutar diagnostico completo de CUDA, AMP FP16 y ONNX Runtime
echo "[4/4] Ejecutando diagnostico de GPU CUDA y Tensor Cores..."
uv run python scripts/check_wsl2_cuda.py

echo "============================================================================"
echo " Entorno WSL 2 listo. Comandos principales:"
echo "   - Iniciar API:       uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
echo "   - Ejecutar Pruebas:  uv run pytest"
echo "   - Abrir Notebooks:   uv run jupyter lab"
echo "============================================================================"
