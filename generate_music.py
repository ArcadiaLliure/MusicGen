import torchaudio
from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write
import time
import os

# Ensure outputs directory exists
os.makedirs("outputs", exist_ok=True)

print("Cargando el modelo MusicGen (esto puede tardar la primera vez)...")
# Usamos el modelo 'small' (300M parameters). Opciones: small, medium, large, melody.
model = MusicGen.get_pretrained('facebook/musicgen-small')

# Configuración de generación
model.set_generation_params(duration=8)  # generar 8 segundos de audio

prompts = [
    '80s pop track with bassy drums and synth',
    'epic orchestral soundtrack with horns and strings',
]

print(f"Generando melodías para los prompts: {prompts}")
start_time = time.time()

# Generamos el audio
wav = model.generate(prompts)

# Guardamos los archivos
for idx, one_wav in enumerate(wav):
    # one_wav shape is [C, T]
    filename = f'outputs/generado_{idx}'
    audio_write(filename, one_wav.cpu(), model.sample_rate, strategy="loudness", loudness_compressor=True)
    print(f"✅ Guardado: {filename}.wav")

end_time = time.time()
print(f"¡Generación completada en {end_time - start_time:.2f} segundos!")
