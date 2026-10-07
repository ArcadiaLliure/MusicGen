import os
import time
import uuid
import threading
import queue
import urllib.request
import urllib.parse
import json
import subprocess
import requests
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_file
from flask_sqlalchemy import SQLAlchemy
from mutagen.wave import WAVE
import mutagen.id3 as id3
import torch
import gc
import torchaudio

from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write

print("Servidor web iniciando (Arcàdia Lliure)...")

app = Flask(__name__)
LIBRARY_DIR = "static/library"
COVERS_DIR = "static/covers"
COMFYUI_MODELS_DIR = "comfyui_data/models/checkpoints"
os.makedirs(LIBRARY_DIR, exist_ok=True)
os.makedirs(COVERS_DIR, exist_ok=True)
os.makedirs(COMFYUI_MODELS_DIR, exist_ok=True)

db_path = os.environ.get("DATABASE_PATH", os.path.abspath(os.path.join(LIBRARY_DIR, "musicgen.db")))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Album(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(255), nullable=False)
    cover_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tracks = db.relationship('Track', backref='album', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        cover = "/" + self.cover_path.replace("\\", "/") if self.cover_path else None
        return {
            'id': self.id,
            'title': self.title,
            'cover_path': cover,
            'created_at': self.created_at.isoformat(),
            'tracks': [t.to_dict() for t in sorted(self.tracks, key=lambda x: x.track_order)]
        }

class Track(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    album_id = db.Column(db.String(36), db.ForeignKey('album.id'), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    artist = db.Column(db.String(255), nullable=True)
    prompt = db.Column(db.Text, nullable=False)
    duration = db.Column(db.Integer, default=30)
    model_name = db.Column(db.String(100), default='facebook/musicgen-melody')
    status = db.Column(db.String(50), default='pending')
    error_msg = db.Column(db.Text, nullable=True)
    filepath = db.Column(db.String(255), nullable=True)
    cover_path = db.Column(db.String(255), nullable=True)
    track_order = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        fp = "/" + self.filepath.replace("\\", "/") if self.filepath else None
        cp = "/" + self.cover_path.replace("\\", "/") if self.cover_path else None
        return {
            'id': self.id,
            'album_id': self.album_id,
            'title': self.title,
            'artist': self.artist,
            'prompt': self.prompt,
            'duration': self.duration,
            'model_name': self.model_name,
            'status': self.status,
            'error_msg': self.error_msg,
            'filepath': fp,
            'cover_path': cp,
            'track_order': self.track_order,
            'created_at': self.created_at.isoformat()
        }

with app.app_context():
    try: db.create_all()
    except: pass
    try:
        db.session.execute(db.text("ALTER TABLE album ADD COLUMN cover_path VARCHAR(255)"))
        db.session.execute(db.text("ALTER TABLE track ADD COLUMN cover_path VARCHAR(255)"))
        db.session.commit()
    except: db.session.rollback()

current_model_name = None
model = None
task_queue = queue.Queue()
active_task_id = None

def get_model(model_name):
    global model, current_model_name
    if model_name != current_model_name or model is None:
        if model is not None:
            del model
            gc.collect()
            if torch.cuda.is_available(): torch.cuda.empty_cache()
        model = MusicGen.get_pretrained(model_name)
        current_model_name = model_name
    return model

def write_metadata(filepath, title, artist, album):
    try:
        audio = WAVE(filepath)
        if audio.tags is None: audio.add_tags()
        audio.tags.add(id3.TIT2(encoding=3, text=title or "Untitled"))
        if artist: audio.tags.add(id3.TPE1(encoding=3, text=artist))
        if album: audio.tags.add(id3.TALB(encoding=3, text=album))
        audio.save()
    except Exception as e: print(f"Error escribiendo metadatos: {e}")

def worker():
    global active_task_id
    with app.app_context():
        while True:
            track_id = task_queue.get()
            active_task_id = track_id
            track = db.session.get(Track, track_id)
            if not track:
                task_queue.task_done()
                continue
            try:
                track.status = 'generating'
                db.session.commit()
                active_model = get_model(track.model_name)
                active_model.set_generation_params(duration=track.duration)
                
                melody_path = None
                if track.album_id and track.track_order > 1:
                    prev_track = Track.query.filter_by(album_id=track.album_id, track_order=track.track_order-1).first()
                    if prev_track and prev_track.status == 'done' and prev_track.filepath:
                        if 'melody' in track.model_name.lower(): melody_path = prev_track.filepath
                
                if melody_path:
                    melody, sr = torchaudio.load(melody_path)
                    wav = active_model.generate_with_chroma([track.prompt], melody[None], sr)
                else:
                    wav = active_model.generate([track.prompt])
                
                album_dir = os.path.join(LIBRARY_DIR, track.album_id or "Singles")
                os.makedirs(album_dir, exist_ok=True)
                filename = f"{track.track_order:02d}_{track.title[:20].replace(' ', '_')}_{int(time.time())}"
                filepath_no_ext = os.path.join(album_dir, filename)
                audio_write(filepath_no_ext, wav[0].cpu(), active_model.sample_rate, strategy="loudness", loudness_compressor=True)
                final_filepath = filepath_no_ext + ".wav"
                album_name = track.album.title if track.album else "Singles"
                write_metadata(final_filepath, track.title, track.artist, album_name)
                track.filepath = final_filepath
                track.status = 'done'
            except Exception as e:
                track.status = 'error'
                track.error_msg = str(e)
            finally:
                db.session.commit()
                active_task_id = None
                task_queue.task_done()

threading.Thread(target=worker, daemon=True).start()

# --- ComfyUI Models ---
COMFYUI_MODELS = {
    "DreamShaper_8_pruned.safetensors": {
        "name": "DreamShaper 8 (Artístic, SD1.5, 2GB)",
        "url": "https://huggingface.co/Lykon/DreamShaper/resolve/main/DreamShaper_8_pruned.safetensors"
    },
    "Juggernaut_XL_v9.safetensors": {
        "name": "Juggernaut XL v9 (Fotorealista, SDXL, 6.6GB)",
        "url": "https://huggingface.co/RunDiffusion/Juggernaut-XL-v9/resolve/main/Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors"
    },
    "RealVisXL_V4.0.safetensors": {
        "name": "RealVisXL V4.0 (Realisme, SDXL, 6.6GB)",
        "url": "https://huggingface.co/SG161222/RealVisXL_V4.0/resolve/main/RealVisXL_V4.0.safetensors"
    },
    "GhostMix_v2.0.safetensors": {
        "name": "GhostMix v2 (Anime/Il·lustració, SD1.5, 2GB)",
        "url": "https://civitai.com/api/download/models/76907"
    },
    "Krea2_Turbo_FP8.safetensors": {
        "name": "Krea 2 Turbo FP8 (Súper Rápido, SDXL-tier, 4GB)",
        "url": "https://civitai.com/api/download/models/3064297"
    },
    "v1-5-pruned-emaonly.safetensors": {
        "name": "SD 1.5 Base (Estàndard, 4GB)",
        "url": "https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors"
    },
    "sd_xl_turbo_1.0_fp16.safetensors": {
        "name": "SDXL Turbo (Ràpid, 3.5GB)",
        "url": "https://huggingface.co/stabilityai/sdxl-turbo/resolve/main/sd_xl_turbo_1.0_fp16.safetensors"
    }
}
download_progress = {"status": "idle", "progress": 0, "file": ""}

def download_file(url, filepath):
    global download_progress
    try:
        download_progress = {"status": "downloading", "progress": 0, "file": os.path.basename(filepath)}
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        # Validar si es un error o bloque de login (ej. < 10MB)
        if total_size < 10 * 1024 * 1024:
            raise Exception("URL inválida o modelo bloqueado por inicio de sesión (tamaño muy pequeño)")
            
        block_size = 1024 * 1024 # 1MB
        written = 0
        with open(filepath, 'wb') as f:
            for data in response.iter_content(block_size):
                f.write(data)
                written += len(data)
                if total_size > 0:
                    download_progress["progress"] = int((written / total_size) * 100)
        download_progress = {"status": "idle", "progress": 0, "file": ""}
    except Exception as e:
        download_progress = {"status": "error", "error": str(e)}
        if os.path.exists(filepath):
            os.remove(filepath)

@app.route("/api/comfyui/models", methods=["GET"])
def get_comfyui_models():
    models_list = []
    for filename, info in COMFYUI_MODELS.items():
        path = os.path.join(COMFYUI_MODELS_DIR, filename)
        is_downloaded = os.path.exists(path)
        models_list.append({
            "filename": filename,
            "name": info["name"],
            "downloaded": is_downloaded
        })
    return jsonify({"models": models_list, "download_status": download_progress})

@app.route("/api/comfyui/download", methods=["POST"])
def download_comfyui_model():
    filename = request.json.get("filename")
    if filename not in COMFYUI_MODELS:
        return jsonify({"error": "Modelo desconocido"}), 400
    if download_progress["status"] == "downloading":
        return jsonify({"error": "Ya hay una descarga en curso"}), 400
    path = os.path.join(COMFYUI_MODELS_DIR, filename)
    url = COMFYUI_MODELS[filename]["url"]
    threading.Thread(target=download_file, args=(url, path), daemon=True).start()
    return jsonify({"success": True})

@app.route("/api/comfyui/delete", methods=["POST"])
def delete_comfyui_model():
    filename = request.json.get("filename")
    if filename not in COMFYUI_MODELS:
        return jsonify({"error": "Modelo desconocido"}), 400
    path = os.path.join(COMFYUI_MODELS_DIR, filename)
    if os.path.exists(path):
        try:
            os.remove(path)
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "No descargado"}), 400

# --- Endpoints API ---

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/generate/single", methods=["POST"])
def generate_single():
    data = request.json
    t = Track(title=data.get('title') or "Untitled Track", artist=data.get('artist') or "Unknown Artist", prompt=data.get('prompt', ''), duration=int(data.get('duration', 30)), model_name=data.get('model', 'facebook/musicgen-melody'), cover_path=data.get('cover_path'))
    db.session.add(t)
    db.session.commit()
    task_queue.put(t.id)
    return jsonify({"success": True, "track": t.to_dict()})

@app.route("/api/generate/album", methods=["POST"])
def generate_album():
    data = request.json
    album = Album(title=data.get('album_title') or "Untitled Album", cover_path=data.get('cover_path'))
    db.session.add(album)
    db.session.flush()
    tracks_data = data.get('tracks', [])
    created_tracks = []
    for idx, t_data in enumerate(tracks_data):
        t = Track(album_id=album.id, title=t_data.get('title') or f"Track {idx+1}", artist=data.get('artist') or "Unknown Artist", prompt=t_data.get('prompt', ''), duration=int(t_data.get('duration', 30)), model_name=data.get('model', 'facebook/musicgen-melody'), track_order=idx+1, cover_path=data.get('cover_path'))
        db.session.add(t)
        created_tracks.append(t)
    db.session.commit()
    for t in created_tracks: task_queue.put(t.id)
    return jsonify({"success": True, "album": album.to_dict()})

@app.route("/api/status", methods=["GET"])
def get_status():
    tracks_in_progress = Track.query.filter(Track.status.in_(['pending', 'generating'])).order_by(Track.created_at).all()
    return jsonify({"queue": [t.to_dict() for t in tracks_in_progress]})

@app.route("/api/library", methods=["GET"])
def get_library():
    albums = Album.query.order_by(Album.created_at.desc()).all()
    singles = Track.query.filter_by(album_id=None).order_by(Track.created_at.desc()).all()
    return jsonify({"albums": [a.to_dict() for a in albums], "singles": [t.to_dict() for t in singles]})

@app.route("/api/tracks/<track_id>", methods=["DELETE"])
def manage_track(track_id):
    track = db.session.get(Track, track_id)
    if not track: return jsonify({"error": "Not found"}), 404
    if track.filepath and os.path.exists(track.filepath): os.remove(track.filepath)
    db.session.delete(track)
    db.session.commit()
    return jsonify({"success": True})

@app.route("/api/albums/<album_id>", methods=["DELETE"])
def manage_album(album_id):
    album = db.session.get(Album, album_id)
    if not album: return jsonify({"error": "Not found"}), 404
    for track in album.tracks:
        if track.filepath and os.path.exists(track.filepath): os.remove(track.filepath)
    album_dir = os.path.join(LIBRARY_DIR, album_id)
    if os.path.exists(album_dir):
        import shutil
        shutil.rmtree(album_dir, ignore_errors=True)
    db.session.delete(album)
    db.session.commit()
    return jsonify({"success": True})

@app.route("/api/upload_cover", methods=["POST"])
def upload_cover():
    if 'file' not in request.files: return jsonify({"error": "No file"}), 400
    file = request.files['file']
    ext = file.filename.split('.')[-1]
    filename = f"cover_{int(time.time())}.{ext}"
    path = os.path.join(COVERS_DIR, filename)
    file.save(path)
    return jsonify({"success": True, "cover_path": path, "url": f"/static/covers/{filename}"})

@app.route("/api/comfyui", methods=["POST"])
def comfyui_generate():
    try:
        prompt_text = request.json.get('prompt', 'beautiful album cover, abstract art')
        ckpt_name = request.json.get('model', 'DreamShaper_8_pruned.safetensors')
        
        # Configure params based on model
        steps = 20
        cfg = 7
        sampler = "euler_ancestral"
        width = 512
        height = 512

        if "xl" in ckpt_name.lower() or "krea" in ckpt_name.lower():
            width = 1024
            height = 1024
        
        if "turbo" in ckpt_name.lower():
            steps = 4
            cfg = 2.0
            sampler = "euler_ancestral"
            
        workflow = {
          "3": {"class_type": "KSampler", "inputs": {"seed": int(time.time()), "steps": steps, "cfg": cfg, "sampler_name": sampler, "scheduler": "normal", "denoise": 1, "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}},
          "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ckpt_name}},
          "5": {"class_type": "EmptyLatentImage", "inputs": {"batch_size": 1, "height": height, "width": width}},
          "6": {"class_type": "CLIPTextEncode", "inputs": {"text": f"masterpiece, high quality album cover, {prompt_text}", "clip": ["4", 1]}},
          "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "bad quality, text, watermark, signature", "clip": ["4", 1]}},
          "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
          "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "musicgen", "images": ["8", 0]}}
        }
        
        target_host = "127.0.0.1:8188"
        try: urllib.request.urlopen("http://127.0.0.1:8188/", timeout=1)
        except:
            pass

        req = urllib.request.Request(f"http://{target_host}/prompt", data=json.dumps({"prompt": workflow}).encode('utf-8'), headers={'Content-Type': 'application/json'})
        res = urllib.request.urlopen(req)
        data = json.loads(res.read())
        prompt_id = data['prompt_id']
        
        for _ in range(60):
            time.sleep(2)
            hist_req = urllib.request.urlopen(f"http://{target_host}/history/{prompt_id}")
            hist_data = json.loads(hist_req.read())
            if prompt_id in hist_data:
                outputs = hist_data[prompt_id]['outputs']
                for node_id, node_output in outputs.items():
                    if 'images' in node_output:
                        img_filename = node_output['images'][0]['filename']
                        img_url = f"http://{target_host}/view?filename={urllib.parse.quote(img_filename)}"
                        img_res = urllib.request.urlopen(img_url)
                        local_filename = f"cover_comfy_{int(time.time())}.png"
                        local_path = os.path.join(COVERS_DIR, local_filename)
                        with open(local_path, 'wb') as f:
                            f.write(img_res.read())
                        return jsonify({"success": True, "cover_path": local_path, "url": f"/static/covers/{local_filename}"})
                        
        return jsonify({"error": "Timeout esperando a ComfyUI"}), 500
    except urllib.error.URLError as e:
        return jsonify({"error": f"ComfyUI està apagat o inaccessible. (detall: {e})"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/export/mp3/<track_id>", methods=["GET"])
def export_mp3(track_id):
    track = db.session.get(Track, track_id)
    if not track or not track.filepath: return "Not found", 404
    mp3_path = track.filepath.replace(".wav", ".mp3")
    if not os.path.exists(mp3_path):
        subprocess.run(["ffmpeg", "-y", "-i", track.filepath, "-b:a", "320k", mp3_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return send_file(mp3_path, as_attachment=True)

@app.route("/api/export/mp4/<track_id>", methods=["GET"])
def export_mp4(track_id):
    track = db.session.get(Track, track_id)
    if not track or not track.filepath: return "Not found", 404
    mp4_path = track.filepath.replace(".wav", ".mp4")
    cover = track.cover_path
    if not cover and track.album_id:
        album = db.session.get(Album, track.album_id)
        if album: cover = album.cover_path
    if not cover or not os.path.exists(cover): return "No cover available to generate video", 400
    if not os.path.exists(mp4_path):
        ext = cover.lower().split('.')[-1]
        if ext in ['gif', 'mp4', 'webm']:
            subprocess.run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", cover, "-i", track.filepath, "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-shortest", mp4_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(["ffmpeg", "-y", "-loop", "1", "-framerate", "1", "-i", cover, "-i", track.filepath, "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-shortest", mp4_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return send_file(mp4_path, as_attachment=True)

# --- COMFYUI STARTUP ---
def start_comfyui():
    COMFY_DIR = "/opt/ComfyUI"
    if not os.path.exists(os.path.join(COMFY_DIR, "main.py")):
        print("Clonando ComfyUI por primera vez...")
        subprocess.run(["rm", "-rf", COMFY_DIR])
        subprocess.run(["git", "clone", "https://github.com/comfyanonymous/ComfyUI.git", COMFY_DIR])
        subprocess.run(["git", "-C", COMFY_DIR, "checkout", "v0.7.0"])
        subprocess.run(["sed", "-i", "s/torch.compiler.is_compiling()/False/g", f"{COMFY_DIR}/comfy/ops.py"])
        # Prevent ComfyUI from breaking audiocraft dependencies
        subprocess.run(["sed", "-i", "/^transformers/d", f"{COMFY_DIR}/requirements.txt"])
        subprocess.run(["sed", "-i", "/^torch$/d", f"{COMFY_DIR}/requirements.txt"])
        subprocess.run(["sed", "-i", "/^torchvision/d", f"{COMFY_DIR}/requirements.txt"])
        subprocess.run(["sed", "-i", "/^torchaudio/d", f"{COMFY_DIR}/requirements.txt"])
        subprocess.run(["sed", "-i", "/^av/d", f"{COMFY_DIR}/requirements.txt"])
        # Install dependencies
        subprocess.run(["pip", "install", "-r", f"{COMFY_DIR}/requirements.txt"])
    
    # El servidor se encargará de descargar modelos a comfyui_data/models/checkpoints.
    # Hacemos que ComfyUI lea de ahí.
    import sys
    env = os.environ.copy()
    
    print("Iniciando ComfyUI en el puerto 8188...")
    extra_yaml = os.path.join(COMFY_DIR, "extra_model_paths.yaml")
    with open(extra_yaml, "w") as f:
        f.write(f"musicgen:\n    base_path: {os.path.abspath('comfyui_data')}\n    checkpoints: models/checkpoints")
    
    subprocess.Popen([sys.executable, "main.py", "--listen", "0.0.0.0", "--extra-model-paths-config", extra_yaml], cwd=COMFY_DIR, env=env)

threading.Thread(target=start_comfyui, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=False)
