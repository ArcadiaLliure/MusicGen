FROM continuumio/miniconda3

# Usamos conda para instalar ffmpeg y PyAV (av) precompilados y compatibles, 
# evitando el infierno de compilación de dependencias C en Linux.
RUN conda install -y -c conda-forge ffmpeg av=11.0.0 python=3.10

WORKDIR /app

# Instalar PyTorch con soporte CUDA 12.1
RUN pip install --no-cache-dir torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --extra-index-url https://download.pytorch.org/whl/cu121

# Al estar "av" ya instalado por conda, pip se saltará su instalación fuente.
# Obligamos a instalar una versión de transformers de 2023/2024 para evitar que rechace PyTorch 2.1.0
RUN pip install --no-cache-dir -U audiocraft gradio flask flask-sqlalchemy mutagen transformers==4.38.2

COPY app.py /app/app.py

EXPOSE 8000

CMD ["python", "app.py"]
