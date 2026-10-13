FROM continuumio/miniconda3

# Usamos conda para instalar ffmpeg y PyAV (av) precompilados y compatibles, 
# evitando el infierno de compilación de dependencias C en Linux.
RUN conda install -y -c conda-forge ffmpeg av=11.0.0 python=3.10 git

WORKDIR /app

# Instalar PyTorch con soporte CUDA 12.1 para MusicGen
RUN pip install --no-cache-dir torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --extra-index-url https://download.pytorch.org/whl/cu121

# Dependencias de MusicGen / Audiocraft / Flask
RUN pip install --no-cache-dir -U audiocraft gradio flask flask-sqlalchemy mutagen transformers==4.38.2 yt-dlp requests

# Copiar uv para gestionar el entorno aislado de ACE-Step 1.5
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Crear entorno aislado para ACE-Step 1.5 con Python 3.11 usando uv
RUN uv venv --python 3.11 /opt/acestep_env

# Instalar PyTorch modern con soporte CUDA en capa cacheada
RUN uv pip install --python /opt/acestep_env \
        torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --extra-index-url https://download.pytorch.org/whl/cu124

# Instalar dependencias de ACE-Step 1.5 en capa cacheada
RUN uv pip install --python /opt/acestep_env \
        fastapi "uvicorn[standard]" diffusers "transformers>=4.51.0,<4.58.0" soundfile loguru einops accelerate numba modelscope toml diskcache python-multipart vector-quantize-pytorch safetensors requests peft scipy matplotlib

# Clonar el servicio oficial de ACE-Step 1.5 (MIT) en /opt/acestep_service
RUN git clone --depth 1 https://github.com/ace-step/ACE-Step-1.5.git /opt/acestep_service

COPY app.py /app/app.py

EXPOSE 8000 8001 8188

CMD ["python", "app.py"]
