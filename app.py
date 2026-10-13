import os
import sys
import time
import uuid
import threading
import queue
import re
import shutil
import zipfile
import tempfile
import urllib.request
import urllib.parse
import json
import subprocess
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, send_file
from flask_sqlalchemy import SQLAlchemy
from mutagen.wave import WAVE
import mutagen.id3 as id3
import torch
import gc
import torchaudio

try:
    from audiocraft.models import MusicGen
    from audiocraft.data.audio import audio_write
except ImportError:
    MusicGen = None
    audio_write = None
from engine_providers import get_provider, compile_prompt, MusicGenProvider, AceStepProvider, YuEProvider

def resolve_engine(model_name):
    if not model_name:
        return 'musicgen'
    m = str(model_name).lower()
    if m.startswith('yue'):
        return 'yue'
    elif m.startswith('acestep'):
        return 'acestep'
    return 'musicgen'

print("Servidor web iniciando (Arcàdia Lliure)...")

app = Flask(__name__)
LIBRARY_DIR = "static/library"
COVERS_DIR = "static/covers"
COMFYUI_MODELS_DIR = "comfyui_data/models/checkpoints"

# Directoris de dades generades: inspiracions, temporals i exportacions.
DATA_DIR = os.environ.get("APP_DATA_DIR", "static")
INSPIRATION_DIR = os.path.join(DATA_DIR, "inspirations")
IMPORT_TMP_DIR = os.path.join(DATA_DIR, "tmp")
EXPORTS_DIR = os.path.join(DATA_DIR, "exports")

for _dir in (LIBRARY_DIR, COVERS_DIR, COMFYUI_MODELS_DIR, INSPIRATION_DIR, IMPORT_TMP_DIR, EXPORTS_DIR):
    os.makedirs(_dir, exist_ok=True)

# Paràmetres centralitzats de l'aplicació.
MAX_INSPIRATION_SECONDS = int(os.environ.get("MAX_INSPIRATION_SECONDS", "30"))
MAX_GENERATION_SECONDS = 600  # límit d'una crida de MusicGen per a edicions
DEFAULT_CLEANUP_DAYS = 30
CLEANUP_CHOICES = (10, 30, 90, 0)  # 0 = mai
DEFAULT_MODEL = 'facebook/musicgen-melody'

db_path = os.environ.get("DATABASE_PATH", os.path.abspath(os.path.join(LIBRARY_DIR, "musicgen.db")))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


def to_web_path(path):
    """Converteix una ruta del disc en una ruta web absoluta (/static/...)."""
    return "/" + path.replace("\\", "/") if path else None


class Album(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(255), nullable=False)
    cover_path = db.Column(db.String(255), nullable=True)
    engine = db.Column(db.String(50), default="musicgen")
    selected_style = db.Column(db.String(100), default="all")
    instrument_states = db.Column(db.Text, nullable=True)
    lyrics = db.Column(db.Text, nullable=True)
    inference_params = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tracks = db.relationship('Track', backref='album', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        """Serialitza l'àlbum i les seves pistes ordenades per posició."""
        tracks_dict = [t.to_dict() for t in sorted(self.tracks, key=lambda x: x.track_order)]
        status = 'TANCAT' if tracks_dict and all(t['status'] == 'done' for t in tracks_dict) else 'OBERT'
        return {
            'id': self.id,
            'title': self.title,
            'cover_path': to_web_path(self.cover_path),
            'engine': self.engine or "musicgen",
            'selected_style': self.selected_style or "all",
            'lyrics': self.lyrics or "",
            'created_at': self.created_at.isoformat(),
            'status': status,
            'tracks': tracks_dict
        }


class Track(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    album_id = db.Column(db.String(36), db.ForeignKey('album.id'), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    artist = db.Column(db.String(255), nullable=True)
    prompt = db.Column(db.Text, nullable=False)
    duration = db.Column(db.Integer, default=30)
    model_name = db.Column(db.String(100), default=DEFAULT_MODEL)
    engine = db.Column(db.String(50), default="musicgen")
    selected_style = db.Column(db.String(100), default="all")
    instrument_states = db.Column(db.Text, nullable=True)
    lyrics = db.Column(db.Text, nullable=True)
    inference_params = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='pending')
    error_msg = db.Column(db.Text, nullable=True)
    filepath = db.Column(db.String(255), nullable=True)
    cover_path = db.Column(db.String(255), nullable=True)
    track_order = db.Column(db.Integer, default=1)
    inspiration_id = db.Column(db.String(36), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Serialitza la pista amb les rutes web del fitxer d'àudio i de la caràtula."""
        return {
            'id': self.id,
            'album_id': self.album_id,
            'title': self.title,
            'artist': self.artist,
            'prompt': self.prompt,
            'duration': self.duration,
            'model_name': self.model_name,
            'engine': self.engine or resolve_engine(self.model_name),
            'selected_style': self.selected_style or "all",
            'lyrics': self.lyrics or "",
            'status': self.status,
            'error_msg': self.error_msg,
            'filepath': to_web_path(self.filepath),
            'cover_path': to_web_path(self.cover_path),
            'track_order': self.track_order,
            'inspiration_id': self.inspiration_id,
            'created_at': self.created_at.isoformat()
        }


class Setting(db.Model):
    """Parell clau-valor per a preferències globals de l'aplicació."""
    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.String(255), nullable=False)


class Inspiration(db.Model):
    """Referència d'àudio reutilitzable (fitxer local, YouTube o fragment d'ambdós)."""
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    source = db.Column(db.String(20), nullable=False)  # 'local' | 'youtube'
    original_url = db.Column(db.Text, nullable=True)
    filepath = db.Column(db.String(255), nullable=False)
    duration = db.Column(db.Float, nullable=False)
    favorite = db.Column(db.Boolean, default=False, nullable=False)
    imported_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Serialitza la inspiració amb les metadades mínimes de la biblioteca."""
        return {
            'id': self.id,
            'name': self.name,
            'source': self.source,
            'original_url': self.original_url,
            'url': to_web_path(self.filepath),
            'duration': round(self.duration, 2),
            'favorite': self.favorite,
            'imported_at': self.imported_at.isoformat(),
            'last_used_at': self.last_used_at.isoformat()
        }


class PendingImport(db.Model):
    """Àudio importat que supera la durada màxima i espera que l'usuari triï un fragment."""
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    source = db.Column(db.String(20), nullable=False)
    original_url = db.Column(db.Text, nullable=True)
    filepath = db.Column(db.String(255), nullable=False)
    duration = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class EditSession(db.Model):
    """Sessió d'edició d'una pista. Guarda la revisió activa i l'historial Desfer/Refer."""
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    track_id = db.Column(db.String(36), db.ForeignKey('track.id'), unique=True, nullable=False)
    active_revision_id = db.Column(db.String(36), nullable=True)  # None = àudio original
    undo_stack = db.Column(db.Text, nullable=False, default='[]')
    redo_stack = db.Column(db.Text, nullable=False, default='[]')
    busy = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    revisions = db.relationship('TrackRevision', backref='session', lazy=True, cascade="all, delete-orphan")


class TrackRevision(db.Model):
    """Revisió temporal d'una pista. Cada operació crea una de nova amb el seu pare."""
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey('edit_session.id'), nullable=False)
    parent_id = db.Column(db.String(36), nullable=True)  # None = àudio original
    operation = db.Column(db.String(20), nullable=False)  # regenerate | modify | extend
    instruction = db.Column(db.Text, nullable=True)
    params = db.Column(db.Text, nullable=True)  # JSON amb paràmetres de l'operació
    filepath = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='pending')
    error_msg = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
    try:
        db.create_all()
    except Exception:
        pass
    for statement in (
        "ALTER TABLE album ADD COLUMN cover_path VARCHAR(255)",
        "ALTER TABLE album ADD COLUMN engine VARCHAR(50) DEFAULT 'musicgen'",
        "ALTER TABLE album ADD COLUMN selected_style VARCHAR(100) DEFAULT 'all'",
        "ALTER TABLE album ADD COLUMN instrument_states TEXT",
        "ALTER TABLE album ADD COLUMN lyrics TEXT",
        "ALTER TABLE album ADD COLUMN inference_params TEXT",
        "ALTER TABLE track ADD COLUMN cover_path VARCHAR(255)",
        "ALTER TABLE track ADD COLUMN inspiration_id VARCHAR(36)",
        "ALTER TABLE track ADD COLUMN engine VARCHAR(50) DEFAULT 'musicgen'",
        "ALTER TABLE track ADD COLUMN selected_style VARCHAR(100) DEFAULT 'all'",
        "ALTER TABLE track ADD COLUMN instrument_states TEXT",
        "ALTER TABLE track ADD COLUMN lyrics TEXT",
        "ALTER TABLE track ADD COLUMN inference_params TEXT",
    ):
        try:
            db.session.execute(db.text(statement))
            db.session.commit()
        except Exception:
            db.session.rollback()

current_model_name = None
model = None
task_queue = queue.Queue()
active_task_id = None


def get_model(model_name):
    """Carrega el model MusicGen indicat i allibera el model anterior de la GPU si cal."""
    global model, current_model_name
    if MusicGen is None:
        raise RuntimeError("Meta AudioCraft (audiocraft) no està instal·lat en aquest entorn.")
    if model_name != current_model_name or model is None:
        if model is not None:
            del model
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        model = MusicGen.get_pretrained(model_name)
        current_model_name = model_name
    return model


def write_metadata(filepath, title, artist, album):
    """Escriu el títol, l'artista i l'àlbum com a etiquetes ID3 dins del fitxer WAV."""
    try:
        audio = WAVE(filepath)
        if audio.tags is None:
            audio.add_tags()
        audio.tags.add(id3.TIT2(encoding=3, text=title or "Untitled"))
        if artist:
            audio.tags.add(id3.TPE1(encoding=3, text=artist))
        if album:
            audio.tags.add(id3.TALB(encoding=3, text=album))
        audio.save()
    except Exception as e:
        print(f"Error escribiendo metadatos: {e}")


def resolve_reference_path(track):
    """Retorna el fitxer de referència melòdica d'una pista, o None si no n'hi ha.

    Prioritat: la pista anterior de l'àlbum (encadenament) i després la
    inspiració activa associada a la pista. Quan s'usa una inspiració,
    se'n registra l'ús per a la política de neteja.

    Args:
        track: instància de Track que s'està generant.

    Returns:
        Ruta del fitxer d'àudio de referència o None.
    """
    if track.album_id and track.track_order > 1:
        prev_track = Track.query.filter_by(album_id=track.album_id, track_order=track.track_order - 1).first()
        if prev_track and prev_track.status == 'done' and prev_track.filepath:
            return prev_track.filepath
    if track.inspiration_id:
        insp = db.session.get(Inspiration, track.inspiration_id)
        if insp and os.path.exists(insp.filepath):
            insp.last_used_at = datetime.utcnow()
            db.session.commit()
            return insp.filepath
    return None


def run_generation(track_id):
    """Genera l'àudio d'una pista i n'actualitza l'estat a la base de dades.

    Encamina automàticament la generació cap a MusicGen o ACE-Step 1.5 segons
    el model seleccionat, enriquint el prompt amb els estils i instruments del catàleg.
    """
    track = db.session.get(Track, track_id)
    if not track:
        return
    try:
        track.status = 'generating'
        db.session.commit()

        # Enriquiment acústic del prompt
        compiled = compile_prompt(
            base_prompt=track.prompt,
            instrument_states=track.instrument_states,
            selected_style=track.selected_style
        )
        track.prompt = compiled

        reference_path = resolve_reference_path(track)
        options = {"reference_path": reference_path}

        provider = get_provider(track.model_name, get_model_fn=get_model, library_dir=LIBRARY_DIR)
        final_filepath = provider.generate(track, options=options)

        track.filepath = final_filepath
        track.status = 'done'
    except Exception as e:
        db.session.rollback()
        failed = db.session.get(Track, track_id)
        if failed:
            failed.status = 'error'
            failed.error_msg = str(e)
    finally:
        db.session.commit()


def worker():
    """Fil de treball que processa la cua de tasques una a una, per no saturar la GPU.

    Cada element de la cua és una tupla (tipus, identificador).
    """
    global active_task_id
    with app.app_context():
        while True:
            kind, item_id = task_queue.get()
            active_task_id = item_id
            try:
                if kind == 'generate':
                    run_generation(item_id)
                elif kind == 'edit':
                    run_edit(item_id)
            except Exception as e:
                print(f"Error inesperat a la cua ({kind}): {e}")
            finally:
                active_task_id = None
                task_queue.task_done()


threading.Thread(target=worker, daemon=True).start()


# --- Tasques en segon pla (importacions i exportacions) ---
JOBS = {}
JOBS_LOCK = threading.Lock()


def create_job(kind):
    """Registra una tasca en segon pla i retorna el seu estat inicial."""
    job = {'id': uuid.uuid4().hex, 'kind': kind, 'status': 'queued', 'progress': 0,
           'message': '', 'result': None, 'error': None}
    with JOBS_LOCK:
        JOBS[job['id']] = job
    return job


def update_job(job_id, **fields):
    """Actualitza els camps d'una tasca registrada de manera segura entre fils."""
    with JOBS_LOCK:
        JOBS[job_id].update(fields)


# --- Àudio: utilitats comunes ---
def normalise_audio(src, dst):
    """Converteix qualsevol fitxer d'àudio o vídeo a WAV mono de 32 kHz amb ffmpeg.

    Args:
        src: ruta del fitxer d'origen.
        dst: ruta del WAV de sortida.

    Raises:
        RuntimeError: si ffmpeg falla o no crea el fitxer.
    """
    result = subprocess.run(["ffmpeg", "-y", "-i", src, "-vn", "-ac", "1", "-ar", "32000", dst],
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if result.returncode != 0 or not os.path.exists(dst):
        detail = result.stderr.decode(errors="ignore")[-300:]
        raise RuntimeError(f"No s'ha pogut processar el fitxer d'àudio: {detail}")


def audio_duration(path):
    """Retorna la durada en segons d'un fitxer d'àudio."""
    info = torchaudio.info(path)
    return info.num_frames / info.sample_rate


def compute_peaks(path, bins=600):
    """Calcula l'amplitud màxima per interval per dibuixar una waveform.

    Args:
        path: ruta del fitxer d'àudio.
        bins: nombre de valors de sortida.

    Returns:
        Llista de floats entre 0 i 1.
    """
    wav, _ = torchaudio.load(path)
    mono = wav.abs().mean(dim=0)
    size = max(1, -(-mono.shape[0] // bins))
    padded = torch.nn.functional.pad(mono, (0, size * bins - mono.shape[0]))
    peaks = padded.reshape(bins, size).max(dim=1).values
    top = float(peaks.max()) or 1.0
    return [round(float(p) / top, 4) for p in peaks]


# --- Inspiracions ---
def create_inspiration(path, name, source, url, duration):
    """Mou un WAV normalitzat a la biblioteca d'inspiracions i en crea el registre.

    Args:
        path: ruta del WAV normalitzat (es mou, no es copia).
        name: nom visible de la inspiració.
        source: 'local' o 'youtube'.
        url: URL original si escau.
        duration: durada en segons.

    Returns:
        Instància d'Inspiration desada.
    """
    final_path = os.path.join(INSPIRATION_DIR, f"{uuid.uuid4().hex}.wav")
    shutil.move(path, final_path)
    insp = Inspiration(name=name, source=source, original_url=url, filepath=final_path, duration=duration)
    db.session.add(insp)
    db.session.commit()
    return insp


def finish_import(normalised_path, name, source, url):
    """Decideix el destí d'un àudio importat segons la seva durada.

    Si cap dins del màxim configurat, es desa directament com a inspiració.
    Si el supera, es desa com a importació pendent perquè l'usuari triï el fragment.

    Args:
        normalised_path: WAV normalitzat, que es mou al destí final.
        name: nom de la peça.
        source: 'local' o 'youtube'.
        url: URL original si escau.

    Returns:
        Diccionari amb 'inspiration_id' o 'import_id' per al client.
    """
    duration = audio_duration(normalised_path)
    if duration <= MAX_INSPIRATION_SECONDS:
        insp = create_inspiration(normalised_path, name, source, url, duration)
        return {"inspiration_id": insp.id, "requires_selection": False}
    pending_path = os.path.join(IMPORT_TMP_DIR, f"pending_{uuid.uuid4().hex}.wav")
    shutil.move(normalised_path, pending_path)
    pending = PendingImport(name=name, source=source, original_url=url, filepath=pending_path, duration=duration)
    db.session.add(pending)
    db.session.commit()
    return {"import_id": pending.id, "requires_selection": True}


def download_youtube_audio(url, work_dir):
    """Descarrega l'àudio d'un vídeo de YouTube amb yt-dlp.

    Args:
        url: URL del vídeo (http o https).
        work_dir: carpeta temporal on es desa la descàrrega.

    Returns:
        Tupla (títol, ruta del fitxer descarregat).

    Raises:
        RuntimeError: si la URL no és vàlida o yt-dlp falla.
    """
    if not url or not url.startswith(("http://", "https://")):
        raise RuntimeError("La URL ha de començar per http:// o https://")
    ytdlp_cmd = [sys.executable, "-m", "yt_dlp"]
    extractor_args = ["--extractor-args", "youtube:player_client=default,ios,android,mweb"]

    title_run = subprocess.run(ytdlp_cmd + ["--no-playlist", "--get-title"] + extractor_args + ["--", url],
                               capture_output=True, text=True, timeout=120)
    if title_run.returncode != 0:
        raise RuntimeError(f"yt-dlp no ha pogut llegir el vídeo: {title_run.stderr[-300:]}")
    title = title_run.stdout.strip().splitlines()[0] if title_run.stdout.strip() else "YouTube"

    out_template = os.path.join(work_dir, "yt_%(id)s.%(ext)s")
    download_run = subprocess.run(ytdlp_cmd + ["--no-playlist", "-x", "--audio-format", "wav",
                                               "-o", out_template] + extractor_args + ["--", url],
                                  capture_output=True, text=True, timeout=900)
    if download_run.returncode != 0:
        raise RuntimeError(f"yt-dlp no ha pogut descarregar l'àudio: {download_run.stderr[-300:]}")
    for filename in os.listdir(work_dir):
        if filename.startswith("yt_"):
            return title, os.path.join(work_dir, filename)
    raise RuntimeError("yt-dlp no ha generat cap fitxer d'àudio")


def run_import_job(job_id, source, url, upload_path, name):
    """Executa una importació (YouTube o fitxer local) en segon pla.

    Args:
        job_id: identificador de la tasca registrada.
        source: 'youtube' o 'local'.
        url: URL de YouTube si escau.
        upload_path: ruta del fitxer pujat si escau.
        name: nom opcional de la inspiració.
    """
    with app.app_context():
        work_dir = tempfile.mkdtemp(dir=IMPORT_TMP_DIR)
        try:
            update_job(job_id, status='running', progress=10, message="Obtenint l'àudio...")
            if source == 'youtube':
                title, raw_path = download_youtube_audio(url, work_dir)
                name = name or title
            else:
                raw_path = upload_path
                name = name or os.path.splitext(os.path.basename(upload_path))[0]
            update_job(job_id, progress=50, message="Normalitzant el format...")
            normalised = os.path.join(work_dir, "normalised.wav")
            normalise_audio(raw_path, normalised)
            update_job(job_id, progress=80, message="Desant la inspiració...")
            result = finish_import(normalised, name, source, url)
            update_job(job_id, status='done', progress=100, message='Importació completada', result=result)
        except Exception as e:
            db.session.rollback()
            update_job(job_id, status='error', error=str(e), message="La importació ha fallat")
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)
            if upload_path and os.path.exists(upload_path):
                os.remove(upload_path)


def get_cleanup_days():
    """Retorna la política de neteja vigent en dies (0 = mai)."""
    setting = db.session.get(Setting, 'inspiration_cleanup_days')
    return int(setting.value) if setting else DEFAULT_CLEANUP_DAYS


def run_inspiration_cleanup():
    """Esborra les inspiracions recents no favorites que no s'han usat dins del termini.

    Només afecta les inspiracions; les pistes generades i els favorits no es toquen.

    Returns:
        Nombre d'inspiracions esborrades.
    """
    days = get_cleanup_days()
    if days == 0:
        return 0
    cutoff = datetime.utcnow() - timedelta(days=days)
    stale = Inspiration.query.filter(Inspiration.favorite.is_(False), Inspiration.last_used_at < cutoff).all()
    for insp in stale:
        if os.path.exists(insp.filepath):
            os.remove(insp.filepath)
        db.session.delete(insp)
    db.session.commit()
    return len(stale)


def recover_interrupted_work():
    """Recupera l'estat després d'un reinici: reencua les feines que estaven pendents
    o generant-se perquè el sistema continuï on ho va deixar."""
    tracks_to_resume = Track.query.filter(Track.status.in_(['pending', 'generating'])).order_by(Track.created_at).all()
    for track in tracks_to_resume:
        track.status = 'pending'
        task_queue.put(('generate', track.id))
        
    revisions_to_resume = TrackRevision.query.filter(TrackRevision.status.in_(['pending', 'generating'])).order_by(TrackRevision.created_at).all()
    for rev in revisions_to_resume:
        rev.status = 'pending'
        task_queue.put(('edit', rev.id))
        
    EditSession.query.filter_by(busy=True).update({'busy': False}, synchronize_session=False)
    db.session.commit()


with app.app_context():
    try:
        recover_interrupted_work()
    except Exception as e:
        db.session.rollback()
        print(f"Recuperació d'estat no disponible: {e}")


with app.app_context():
    try:
        run_inspiration_cleanup()
    except Exception as e:
        db.session.rollback()
        print(f"Neteja d'inspiracions no disponible: {e}")


@app.route("/api/jobs/<job_id>", methods=["GET"])
def get_job(job_id):
    """Retorna l'estat actual d'una tasca en segon pla."""
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job:
            return jsonify({"error": "Tasca no trobada"}), 404
        return jsonify(dict(job))


@app.route("/api/inspirations", methods=["GET"])
def list_inspirations():
    """Retorna favorits i recents, aplicant abans la política de neteja."""
    run_inspiration_cleanup()
    favorites = Inspiration.query.filter_by(favorite=True).order_by(Inspiration.last_used_at.desc()).all()
    recents = Inspiration.query.filter_by(favorite=False).order_by(Inspiration.last_used_at.desc()).all()
    return jsonify({
        "favorites": [i.to_dict() for i in favorites],
        "recents": [i.to_dict() for i in recents],
        "cleanup_days": get_cleanup_days(),
        "max_seconds": MAX_INSPIRATION_SECONDS,
    })


@app.route("/api/inspirations/youtube", methods=["POST"])
def import_inspiration_youtube():
    """Inicia la importació d'un vídeo de YouTube com a inspiració."""
    data = request.json or {}
    url = (data.get('url') or '').strip()
    job = create_job('inspiration_import')
    threading.Thread(target=run_import_job, args=(job['id'], 'youtube', url, None, data.get('name')), daemon=True).start()
    return jsonify({"success": True, "job_id": job['id']})


@app.route("/api/inspirations/upload", methods=["POST"])
def import_inspiration_file():
    """Desa un fitxer local pujat i inicia la seva importació en segon pla."""
    uploaded = request.files.get('file')
    if not uploaded:
        return jsonify({"error": "No s'ha rebut cap fitxer"}), 400
    extension = os.path.splitext(uploaded.filename or '')[1].lower()[:10]
    tmp_path = os.path.join(IMPORT_TMP_DIR, f"upload_{uuid.uuid4().hex}{extension}")
    uploaded.save(tmp_path)
    job = create_job('inspiration_import')
    threading.Thread(target=run_import_job, args=(job['id'], 'local', None, tmp_path, request.form.get('name')), daemon=True).start()
    return jsonify({"success": True, "job_id": job['id']})


@app.route("/api/inspirations/imports/<import_id>", methods=["GET"])
def get_pending_import(import_id):
    """Retorna les dades necessàries per al selector temporal: waveform i durada."""
    pending = db.session.get(PendingImport, import_id)
    if not pending:
        return jsonify({"error": "Importació no trobada"}), 404
    return jsonify({
        "id": pending.id,
        "name": pending.name,
        "duration": round(pending.duration, 3),
        "max_seconds": MAX_INSPIRATION_SECONDS,
        "peaks": compute_peaks(pending.filepath),
        "audio_url": f"/api/inspirations/imports/{pending.id}/audio",
    })


@app.route("/api/inspirations/imports/<import_id>/audio", methods=["GET"])
def get_pending_import_audio(import_id):
    """Serveix l'àudio complet d'una importació pendent per escoltar-lo al selector."""
    pending = db.session.get(PendingImport, import_id)
    if not pending:
        return "Not found", 404
    return send_file(pending.filepath, mimetype="audio/wav")


@app.route("/api/inspirations/imports/<import_id>/accept", methods=["POST"])
def accept_pending_import(import_id):
    """Crea el fragment derivat a partir de la selecció de l'usuari i el registra com a inspiració.

    El fragment ha de tenir entre 1 segon i el màxim configurat. Un cop creat,
    s'esborra l'àudio complet de la importació.
    """
    pending = db.session.get(PendingImport, import_id)
    if not pending:
        return jsonify({"error": "Importació no trobada"}), 404
    data = request.json or {}
    try:
        start = float(data.get('start', 0))
        end = float(data.get('end', 0))
    except (TypeError, ValueError):
        return jsonify({"error": "Temps no vàlids"}), 400
    length = end - start
    if start < 0 or end > pending.duration + 0.01 or length < 1 or length > MAX_INSPIRATION_SECONDS + 0.001:
        return jsonify({"error": f"La selecció ha de durar entre 1 i {MAX_INSPIRATION_SECONDS} segons"}), 400

    wav, sr = torchaudio.load(pending.filepath)
    clip = wav[:, int(start * sr):int(end * sr)]
    final_path = os.path.join(INSPIRATION_DIR, f"{uuid.uuid4().hex}.wav")
    temp_path = final_path + ".tmp.wav"
    torchaudio.save(temp_path, clip, sr)
    os.replace(temp_path, final_path)

    insp = Inspiration(name=(data.get('name') or pending.name), source=pending.source,
                       original_url=pending.original_url, filepath=final_path,
                       duration=clip.shape[-1] / sr)
    db.session.add(insp)
    if os.path.exists(pending.filepath):
        os.remove(pending.filepath)
    db.session.delete(pending)
    db.session.commit()
    return jsonify({"success": True, "inspiration": insp.to_dict()})


@app.route("/api/inspirations/imports/<import_id>", methods=["DELETE"])
def discard_pending_import(import_id):
    """Descarta una importació pendent i esborra el seu àudio temporal."""
    pending = db.session.get(PendingImport, import_id)
    if pending:
        if os.path.exists(pending.filepath):
            os.remove(pending.filepath)
        db.session.delete(pending)
        db.session.commit()
    return jsonify({"success": True})


@app.route("/api/inspirations/<insp_id>/favorite", methods=["POST"])
def set_inspiration_favorite(insp_id):
    """Marca o desmarca una inspiració com a favorita."""
    insp = db.session.get(Inspiration, insp_id)
    if not insp:
        return jsonify({"error": "Not found"}), 404
    insp.favorite = bool((request.json or {}).get('favorite', True))
    db.session.commit()
    return jsonify({"success": True, "inspiration": insp.to_dict()})


@app.route("/api/inspirations/<insp_id>/use", methods=["POST"])
def use_inspiration(insp_id):
    """Registra l'ús d'una inspiració en activar-la, per a la política de neteja."""
    insp = db.session.get(Inspiration, insp_id)
    if not insp:
        return jsonify({"error": "Not found"}), 404
    insp.last_used_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"success": True, "inspiration": insp.to_dict()})


@app.route("/api/inspirations/<insp_id>", methods=["DELETE"])
def delete_inspiration(insp_id):
    """Esborra una inspiració i el seu fitxer d'àudio."""
    insp = db.session.get(Inspiration, insp_id)
    if not insp:
        return jsonify({"error": "Not found"}), 404
    if os.path.exists(insp.filepath):
        os.remove(insp.filepath)
    db.session.delete(insp)
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/settings/inspiration-cleanup", methods=["GET", "POST"])
def inspiration_cleanup_setting():
    """Llegeix o modifica la política de neteja d'inspiracions recents."""
    if request.method == "GET":
        return jsonify({"days": get_cleanup_days(), "choices": list(CLEANUP_CHOICES)})
    days = (request.json or {}).get('days')
    if days not in CLEANUP_CHOICES:
        return jsonify({"error": "Valor de neteja no vàlid"}), 400
    setting = db.session.get(Setting, 'inspiration_cleanup_days')
    if setting:
        setting.value = str(days)
    else:
        db.session.add(Setting(key='inspiration_cleanup_days', value=str(days)))
    db.session.commit()
    run_inspiration_cleanup()
    return jsonify({"success": True, "days": days})


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
    """Descarrega un model de ComfyUI per blocs i n'informa del progrés global.

    Args:
        url: URL del fitxer del model.
        filepath: destí local del fitxer.
    """
    global download_progress
    try:
        download_progress = {"status": "downloading", "progress": 0, "file": os.path.basename(filepath)}
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))

        # Validar si es un error o bloque de login (ej. < 10MB)
        if total_size < 10 * 1024 * 1024:
            raise Exception("URL inválida o modelo bloqueado por inicio de sesión (tamaño muy pequeño)")

        block_size = 1024 * 1024
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
    """Llista els models de ComfyUI disponibles i indica quins estan descarregats."""
    models_list = []
    for filename, info in COMFYUI_MODELS.items():
        path = os.path.join(COMFYUI_MODELS_DIR, filename)
        models_list.append({
            "filename": filename,
            "name": info["name"],
            "downloaded": os.path.exists(path)
        })
    return jsonify({"models": models_list, "download_status": download_progress})


@app.route("/api/comfyui/download", methods=["POST"])
def download_comfyui_model():
    """Inicia la descàrrega en segon pla d'un model de ComfyUI."""
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
    """Esborra un model de ComfyUI del disc per alliberar espai."""
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
    """Serveix la interfície principal de l'aplicació."""
    return render_template("index.html")


@app.route("/api/generate/single", methods=["POST"])
def generate_single():
    """Afegeix una pista individual a la cua de generació, amb inspiració opcional."""
    data = request.json or {}
    model_name = data.get('model', DEFAULT_MODEL)
    engine = resolve_engine(model_name)
    inst_states = json.dumps(data.get('instrument_states', {})) if isinstance(data.get('instrument_states'), dict) else (data.get('instrument_states') or '')

    t = Track(
        title=data.get('title') or "Untitled Track",
        artist=data.get('artist') or "Unknown Artist",
        prompt=data.get('prompt', ''),
        duration=int(data.get('duration', 30)),
        model_name=model_name,
        engine=engine,
        selected_style=data.get('style', 'all'),
        lyrics=data.get('lyrics', ''),
        instrument_states=inst_states,
        cover_path=data.get('cover_path'),
        inspiration_id=data.get('inspiration_id') or None
    )
    db.session.add(t)
    db.session.commit()
    task_queue.put(('generate', t.id))
    return jsonify({"success": True, "track": t.to_dict()})


@app.route("/api/generate/album", methods=["POST"])
def generate_album():
    """Crea un àlbum manual o n'actualitza un d'existent afegint-hi pistes.

    La inspiració opcional només s'aplica a la primera pista nova; la resta s'encadenen.
    """
    data = request.json or {}
    album_id = data.get('album_id')
    model_name = data.get('model', DEFAULT_MODEL)
    engine = resolve_engine(model_name)
    selected_style = data.get('style', 'all')
    lyrics = data.get('lyrics', '')
    inst_states = json.dumps(data.get('instrument_states', {})) if isinstance(data.get('instrument_states'), dict) else (data.get('instrument_states') or '')
    
    if album_id:
        album = db.session.get(Album, album_id)
        if not album:
            return jsonify({"error": "Àlbum no trobat"}), 404
        start_idx = len(album.tracks)
        if data.get('cover_path'):
            album.cover_path = data.get('cover_path')
        album.engine = engine
        album.selected_style = selected_style
    else:
        album_title = (data.get('album_title') or '').strip()
        if not album_title:
            return jsonify({"error": "El nom de l'àlbum és obligatori"}), 400
        album = Album(
            title=album_title,
            cover_path=data.get('cover_path'),
            engine=engine,
            selected_style=selected_style,
            instrument_states=inst_states,
            lyrics=lyrics
        )
        db.session.add(album)
        db.session.flush()
        start_idx = 0

    created_tracks = []
    for idx, t_data in enumerate(data.get('tracks', [])):
        t_states = json.dumps(t_data.get('instrument_states', {})) if isinstance(t_data.get('instrument_states'), dict) else (t_data.get('instrument_states') or inst_states)
        t = Track(
            album_id=album.id,
            title=t_data.get('title') or f"Track {start_idx+idx+1}",
            artist=data.get('artist') or "Unknown Artist",
            prompt=t_data.get('prompt', ''),
            duration=int(t_data.get('duration', 30)),
            model_name=model_name,
            engine=engine,
            selected_style=selected_style,
            lyrics=t_data.get('lyrics') or lyrics,
            instrument_states=t_states,
            track_order=start_idx+idx+1,
            cover_path=data.get('cover_path'),
            inspiration_id=(data.get('inspiration_id') or None) if idx == 0 and start_idx == 0 else None
        )
        db.session.add(t)
        created_tracks.append(t)
    db.session.commit()
    for t in created_tracks:
        task_queue.put(('generate', t.id))
    return jsonify({"success": True, "album": album.to_dict()})


@app.route("/api/status", methods=["GET"])
def get_status():
    """Retorna les pistes pendents o en generació."""
    tracks_in_progress = Track.query.filter(Track.status.in_(['pending', 'generating'])).order_by(Track.created_at).all()
    return jsonify({"queue": [t.to_dict() for t in tracks_in_progress]})


@app.route("/api/library", methods=["GET"])
def get_library():
    """Retorna la biblioteca: àlbums amb les seves pistes i pistes soltes."""
    albums = Album.query.order_by(Album.created_at.desc()).all()
    singles = Track.query.filter_by(album_id=None).order_by(Track.created_at.desc()).all()
    return jsonify({"albums": [a.to_dict() for a in albums], "singles": [t.to_dict() for t in singles]})


@app.route("/api/tracks/<track_id>", methods=["DELETE"])
def manage_track(track_id):
    """Esborra una pista i el seu fitxer d'àudio."""
    track = db.session.get(Track, track_id)
    if not track:
        return jsonify({"error": "Not found"}), 404
    discard_edit_session(track)
    if track.filepath and os.path.exists(track.filepath):
        os.remove(track.filepath)
    db.session.delete(track)
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/albums/<album_id>", methods=["DELETE"])
def manage_album(album_id):
    """Esborra un àlbum sencer, les seves pistes i la carpeta d'àudio associada."""
    album = db.session.get(Album, album_id)
    if not album:
        return jsonify({"error": "Not found"}), 404
    for track in album.tracks:
        if track.filepath and os.path.exists(track.filepath):
            os.remove(track.filepath)
    album_dir = os.path.join(LIBRARY_DIR, album_id)
    if os.path.exists(album_dir):
        shutil.rmtree(album_dir, ignore_errors=True)
    for track in album.tracks:
        discard_edit_session(track)
    db.session.delete(album)
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/upload_cover", methods=["POST"])
def upload_cover():
    """Desa una caràtula o un vídeo loop pujat per l'usuari."""
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files['file']
    ext = file.filename.split('.')[-1]
    filename = f"cover_{int(time.time())}.{ext}"
    path = os.path.join(COVERS_DIR, filename)
    file.save(path)
    return jsonify({"success": True, "cover_path": path, "url": f"/static/covers/{filename}"})


@app.route("/api/comfyui", methods=["POST"])
def comfyui_generate():
    """Genera una caràtula amb ComfyUI i la desa a la carpeta de caràtules."""
    try:
        prompt_text = request.json.get('prompt', 'beautiful album cover, abstract art')
        ckpt_name = request.json.get('model', 'DreamShaper_8_pruned.safetensors')

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
        try:
            urllib.request.urlopen("http://127.0.0.1:8188/", timeout=1)
        except Exception:
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


# --- Exportació d'arxius per pista (reutilitzada per a MP3/MP4 individuals i per a àlbums) ---
JOB_FILES = {}  # job_id -> (ruta del fitxer, nom de descàrrega)


def safe_filename(text, fallback="sense_nom"):
    """Neteja un text perquè es pugui usar com a nom de fitxer o carpeta.

    Args:
        text: text original (títol de pista o d'àlbum).
        fallback: valor si el text queda buit després de netejar-lo.

    Returns:
        Nom segur de fins a 80 caràcters.
    """
    cleaned = re.sub(r'[\\/:*?"<>|\x00-\x1f]', '', text or '').strip().rstrip('.')
    return cleaned[:80] or fallback


def run_ffmpeg(command):
    """Executa una ordre de ffmpeg i llança un error comprensible si falla.

    Args:
        command: llista d'arguments per a subprocess.

    Raises:
        RuntimeError: si ffmpeg retorna un codi d'error.
    """
    result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg ha fallat: {result.stderr.decode(errors='ignore')[-300:]}")


def ensure_track_export(track, fmt):
    """Genera (si cal) l'exportació d'una pista en MP3 o MP4 i en retorna la ruta.

    Els fitxers ja existents es reutilitzen. El MP4 necessita una caràtula
    pròpia de la pista o de l'àlbum.

    Args:
        track: pista amb fitxer d'àudio completat.
        fmt: 'mp3' o 'mp4'.

    Returns:
        Ruta del fitxer exportat.

    Raises:
        RuntimeError: si falta la caràtula per a MP4 o ffmpeg falla.
    """
    base = track.filepath[:-len(".wav")]
    if fmt == 'mp3':
        out_path = base + ".mp3"
        if not (os.path.exists(out_path) and os.path.getsize(out_path) > 0):
            if os.path.exists(out_path):
                try:
                    os.remove(out_path)
                except OSError:
                    pass
            run_ffmpeg(["ffmpeg", "-y", "-i", track.filepath, "-b:a", "320k", out_path])
        return out_path

    cover = track.cover_path or (track.album.cover_path if track.album else None)
    if cover and cover.startswith('/'):
        cover = cover.lstrip('/')
    if not cover or not os.path.exists(cover):
        raise RuntimeError(f"Falta la caràtula per exportar '{track.title}' en MP4")
    out_path = base + ".mp4"
    if not (os.path.exists(out_path) and os.path.getsize(out_path) > 0):
        if os.path.exists(out_path):
            try:
                os.remove(out_path)
            except OSError:
                pass
        try:
            if cover.lower().split('.')[-1] in ['gif', 'mp4', 'webm']:
                run_ffmpeg(["ffmpeg", "-y", "-stream_loop", "-1", "-i", cover, "-i", track.filepath,
                            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                            "-c:v", "libx264", "-preset", "veryfast", "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-shortest", out_path])
            else:
                run_ffmpeg(["ffmpeg", "-y", "-loop", "1", "-framerate", "1", "-i", cover, "-i", track.filepath,
                            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                            "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage", "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-shortest", out_path])
        except Exception:
            if os.path.exists(out_path) and os.path.getsize(out_path) == 0:
                try:
                    os.remove(out_path)
                except OSError:
                    pass
            raise
    return out_path


@app.route("/api/export/mp3/<track_id>", methods=["GET"])
def export_mp3(track_id):
    """Descarrega una pista en MP3 (320 kbps)."""
    track = db.session.get(Track, track_id)
    if not track or not track.filepath:
        return "Not found", 404
    try:
        path = ensure_track_export(track, 'mp3')
    except RuntimeError as e:
        return str(e), 500
    fname = f"{safe_filename(track.title, 'pista')}.mp3"
    return send_file(path, as_attachment=True, download_name=fname, mimetype="audio/mpeg")


@app.route("/api/export/mp4/<track_id>", methods=["GET"])
def export_mp4(track_id):
    """Descarrega una pista en MP4 amb la caràtula com a imatge o vídeo de fons."""
    track = db.session.get(Track, track_id)
    if not track or not track.filepath:
        return "Not found", 404
    try:
        path = ensure_track_export(track, 'mp4')
    except RuntimeError as e:
        return str(e), 400
    fname = f"{safe_filename(track.title, 'pista')}.mp4"
    return send_file(path, as_attachment=True, download_name=fname, mimetype="video/mp4")


@app.route("/api/generate/album/auto", methods=["POST"])
def generate_album_auto():
    """Crea un àlbum en mode automàtic o n'actualitza un d'existent afegint-hi N pistes."""
    data = request.json or {}
    model_name = data.get('model', DEFAULT_MODEL)
    engine = resolve_engine(model_name)
    selected_style = data.get('style', 'all')
    lyrics = data.get('lyrics', '')
    inst_states = json.dumps(data.get('instrument_states', {})) if isinstance(data.get('instrument_states'), dict) else (data.get('instrument_states') or '')
    
    album_id = data.get('album_id')
    if album_id:
        album = db.session.get(Album, album_id)
        if not album:
            return jsonify({"error": "Àlbum no trobat"}), 404
        start_idx = len(album.tracks)
        if data.get('cover_path'):
            album.cover_path = data.get('cover_path')
        album.engine = engine
        album.selected_style = selected_style
    else:
        album_title = (data.get('album_title') or '').strip()
        if not album_title:
            return jsonify({"error": "El nom de l'àlbum és obligatori"}), 400
        album = Album(
            title=album_title,
            cover_path=data.get('cover_path'),
            engine=engine,
            selected_style=selected_style,
            instrument_states=inst_states,
            lyrics=lyrics
        )
        db.session.add(album)
        db.session.flush()
        start_idx = 0

    global_prompt = (data.get('global_prompt') or '').strip()
    if not global_prompt:
        return jsonify({"error": "Cal un prompt global per a l'àlbum"}), 400
    try:
        track_count = int(data.get('track_count', 1))
        duration = int(data.get('duration', 30))
    except (TypeError, ValueError):
        return jsonify({"error": "Nombre de pistes o durada no vàlids"}), 400
    if not 1 <= track_count <= 20:
        return jsonify({"error": "El nombre de pistes ha d'estar entre 1 i 20"}), 400
    if not 1 <= duration <= MAX_GENERATION_SECONDS:
        return jsonify({"error": f"La durada ha d'estar entre 1 i {MAX_GENERATION_SECONDS} segons"}), 400

    instrument_prefix = (data.get('instrument_prefix') or '').strip()
    prompt = f"{instrument_prefix} {global_prompt}".strip()
    
    created = []
    for i in range(1, track_count + 1):
        actual_order = start_idx + i
        track = Track(
            album_id=album.id,
            title=f"{album.title}_{actual_order}",
            artist=data.get('artist') or "Unknown Artist",
            prompt=prompt,
            duration=duration,
            model_name=model_name,
            engine=engine,
            selected_style=selected_style,
            lyrics=lyrics,
            instrument_states=inst_states,
            track_order=actual_order,
            cover_path=data.get('cover_path'),
            inspiration_id=(data.get('inspiration_id') or None) if i == 1 and start_idx == 0 else None
        )
        db.session.add(track)
        created.append(track)
    db.session.commit()
    for track in created:
        task_queue.put(('generate', track.id))
    return jsonify({"success": True, "album": album.to_dict()})


@app.route("/api/albums/<album_id>", methods=["PATCH"])
def rename_album(album_id):
    """Canvia el nom d'un àlbum i actualitza l'etiqueta d'àlbum de les pistes completades."""
    album = db.session.get(Album, album_id)
    if not album:
        return jsonify({"error": "Not found"}), 404
    title = ((request.json or {}).get('title') or '').strip()
    if not title:
        return jsonify({"error": "El nom no pot estar buit"}), 400
    album.title = title
    db.session.commit()
    for track in album.tracks:
        if track.filepath and os.path.exists(track.filepath):
            write_metadata(track.filepath, track.title, track.artist, title)
    return jsonify({"success": True, "album": album.to_dict()})


@app.route("/api/tracks/<track_id>", methods=["PATCH"])
def rename_track(track_id):
    """Canvia el nom d'una pista i actualitza les seves etiquetes ID3."""
    track = db.session.get(Track, track_id)
    if not track:
        return jsonify({"error": "Not found"}), 404
    title = ((request.json or {}).get('title') or '').strip()
    if not title:
        return jsonify({"error": "El nom no pot estar buit"}), 400
    track.title = title
    db.session.commit()
    if track.filepath and os.path.exists(track.filepath):
        album_name = track.album.title if track.album else "Singles"
        write_metadata(track.filepath, title, track.artist, album_name)
    return jsonify({"success": True, "track": track.to_dict()})



def run_youtube_export(job_id, album_id):
    """Genera un sol fitxer de vdeo per YouTube amb l'lbum sencer concatenat."""
    with app.app_context():
        try:
            album = db.session.get(Album, album_id)
            if not album:
                raise RuntimeError("?lbum no trobat")
            tracks = sorted(album.tracks, key=lambda t: t.track_order)
            if not tracks:
                raise RuntimeError("L'lbum no tǸ pistes")
            incomplete = [t.title for t in tracks if t.status != 'done' or not t.filepath]
            if incomplete:
                raise RuntimeError("Hi ha pistes sense completar: " + ", ".join(incomplete))
            
            cover = album.cover_path
            if not cover:
                for t in tracks:
                    if t.cover_path:
                        cover = t.cover_path
                        break
            if cover and cover.startswith('/'):
                cover = cover.lstrip('/')
            if not cover or not os.path.exists(cover):
                raise RuntimeError("Falta la caràtula per exportar el vídeo a YouTube")
            
            update_job(job_id, status='running', progress=10, message="Concatenant pistes d'àudio...")
            
            # Create a list file for ffmpeg concat
            album_folder = safe_filename(album.title, "Album")
            list_file_path = os.path.join(EXPORTS_DIR, f"list_{job_id[:8]}.txt")
            with open(list_file_path, 'w', encoding='utf-8') as f:
                for t in tracks:
                    # ffmpeg requires absolute paths or relative paths in the text file, 
                    # but escaping can be tricky. It's safe to use single quotes and replace internal single quotes
                    safe_path = os.path.abspath(t.filepath).replace("'", "'\\''")
                    f.write(f"file '{safe_path}'\n")
            
            concat_audio_path = os.path.join(EXPORTS_DIR, f"concat_{job_id[:8]}.wav")
            run_ffmpeg(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file_path, "-c", "copy", concat_audio_path])
            
            update_job(job_id, progress=50, message="Muntant el vídeo per a YouTube...")
            
            out_video_path = os.path.join(EXPORTS_DIR, f"{album_folder}_YouTube_{job_id[:8]}.mp4")
            
            # Combine audio with video/image loop
            if cover.lower().split('.')[-1] in ['gif', 'mp4', 'webm']:
                run_ffmpeg(["ffmpeg", "-y", "-stream_loop", "-1", "-i", cover, "-i", concat_audio_path,
                            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                            "-c:v", "libx264", "-preset", "veryfast", "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-shortest", out_video_path])
            else:
                run_ffmpeg(["ffmpeg", "-y", "-loop", "1", "-framerate", "1", "-i", cover, "-i", concat_audio_path,
                            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                            "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage", "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-shortest", out_video_path])
            
            os.remove(list_file_path)
            os.remove(concat_audio_path)
            
            JOB_FILES[job_id] = (out_video_path, f"{album_folder}_YouTube.mp4")
            update_job(job_id, status='done', progress=100, message="Vdeo de YouTube exportat correctament",
                       result={"download_url": f"/api/jobs/{job_id}/download", "filename": f"{album_folder}_YouTube.mp4"})
            
        except Exception as e:
            db.session.rollback()
            update_job(job_id, status='error', error=str(e), message="L'exportaci a YouTube ha fallat")


def run_album_export(job_id, album_id, fmt):
    """Exporta totes les pistes d'un àlbum en un ZIP en segon pla.

    El ZIP conté una carpeta amb el nom de l'àlbum i fitxers numerats segons
    l'ordre de les pistes. Si alguna pista no està completa o no es pot
    exportar, la tasca falla i no es crea cap ZIP incomplet.

    Args:
        job_id: identificador de la tasca registrada.
        album_id: identificador de l'àlbum a exportar.
        fmt: 'mp3' o 'mp4'.
    """
    with app.app_context():
        tmp_zip = None
        try:
            album = db.session.get(Album, album_id)
            if not album:
                raise RuntimeError("Àlbum no trobat")
            tracks = sorted(album.tracks, key=lambda t: t.track_order)
            if not tracks:
                raise RuntimeError("L'àlbum no té pistes")
            incomplete = [t.title for t in tracks if t.status != 'done' or not t.filepath]
            if incomplete:
                raise RuntimeError("Hi ha pistes sense completar: " + ", ".join(incomplete))

            album_folder = safe_filename(album.title, "Album")
            entries = []
            for i, track in enumerate(tracks, start=1):
                update_job(job_id, status='running', progress=int(90 * (i - 1) / len(tracks)),
                           message=f"Exportant pista {i} de {len(tracks)}...")
                source = ensure_track_export(track, fmt)
                entries.append((source, f"{album_folder}/{i:02d} - {safe_filename(track.title, 'Pista')}.{fmt}"))

            update_job(job_id, progress=92, message="Creant el fitxer ZIP...")
            zip_path = os.path.join(EXPORTS_DIR, f"{album_folder}_{fmt}_{job_id[:8]}.zip")
            tmp_zip = zip_path + ".tmp"
            with zipfile.ZipFile(tmp_zip, 'w', compression=zipfile.ZIP_STORED) as zf:
                for source, arcname in entries:
                    zf.write(source, arcname)
            os.replace(tmp_zip, zip_path)
            tmp_zip = None

            JOB_FILES[job_id] = (zip_path, f"{album_folder}.zip")
            update_job(job_id, status='done', progress=100, message="Àlbum exportat",
                       result={"download_url": f"/api/jobs/{job_id}/download", "filename": f"{album_folder}.zip"})
        except Exception as e:
            db.session.rollback()
            if tmp_zip and os.path.exists(tmp_zip):
                os.remove(tmp_zip)
            update_job(job_id, status='error', error=str(e), message="L'exportació ha fallat")


@app.route("/api/albums/<album_id>/export", methods=["POST"])
def export_album(album_id):
    """Inicia l'exportaci completa d'un lbum en MP3, MP4 o YT com a tasca en segon pla."""
    album = db.session.get(Album, album_id)
    if not album:
        return jsonify({"error": "Not found"}), 404
    fmt = ((request.json or {}).get('format') or 'mp3').lower()
    if fmt not in ('mp3', 'mp4', 'yt'):
        return jsonify({"error": "Format no suportat"}), 400
    job = create_job('album_export')
    if fmt == 'yt':
        threading.Thread(target=run_youtube_export, args=(job['id'], album_id), daemon=True).start()
    else:
        threading.Thread(target=run_album_export, args=(job['id'], album_id, fmt), daemon=True).start()
    return jsonify({"success": True, "job_id": job['id']})


@app.route("/api/jobs/<job_id>/download", methods=["GET"])
def download_job_file(job_id):
    """Descarrega el fitxer produït per una tasca finalitzada."""
    entry = JOB_FILES.get(job_id)
    if not entry or not os.path.exists(entry[0]):
        return "Not found", 404
    return send_file(entry[0], as_attachment=True, download_name=entry[1])




# --- Editor de cançó: historial temporal no destructiu ---
EXPERIMENTAL_WARNING = ("La modificació parcial és experimental. Es poden produir canvis bruscos de melodia, "
                        "ritme, timbre o mescla als punts d'unió.")
REGENERATE_WARNING = ("En regenerar tota la cançó, el resultat intentarà conservar la identitat de la referència, "
                      "però la melodia, l'estructura, els arranjaments o la interpretació poden canviar.")


class EditBusyError(Exception):
    """Es llança quan ja hi ha una operació d'edició en curs sobre la pista."""


def remove_file(path):
    """Esborra un fitxer si existeix."""
    if path and os.path.exists(path):
        os.remove(path)


def load_stack(raw):
    """Converteix l'historial guardat com a JSON en una llista."""
    return json.loads(raw or '[]')


def get_edit_session(track, create=False):
    """Retorna la sessió d'edició d'una pista, creant-la si cal."""
    session = EditSession.query.filter_by(track_id=track.id).first()
    if session is None and create:
        session = EditSession(track_id=track.id)
        db.session.add(session)
        db.session.commit()
    return session


def active_audio_path(track, session):
    """Retorna el fitxer de la versió activa, o l'original si no hi ha cap revisió activa."""
    if session and session.active_revision_id:
        rev = db.session.get(TrackRevision, session.active_revision_id)
        if rev and rev.filepath and rev.status == 'done':
            return rev.filepath
    return track.filepath


def revision_base_path(track, rev):
    """Retorna el fitxer del pare d'una revisió (l'original si el pare és None)."""
    if rev.parent_id:
        parent = db.session.get(TrackRevision, rev.parent_id)
        if parent and parent.filepath:
            return parent.filepath
    return track.filepath


def discard_edit_session(track):
    """Esborra totes les revisions temporals d'una pista. L'original no es modifica."""
    session = get_edit_session(track)
    if session:
        for rev in session.revisions:
            remove_file(rev.filepath)
        db.session.delete(session)
        db.session.commit()


def remove_cached_exports(track):
    """Esborra els MP3 i MP4 generats per a una versió anterior de la pista."""
    base = track.filepath[:-len(".wav")]
    for ext in (".mp3", ".mp4"):
        remove_file(base + ext)


def match_channels(wav, channels):
    """Adapta el nombre de canals d'un tensor d'àudio al de la referència."""
    if wav.shape[0] == channels:
        return wav
    if wav.shape[0] == 1:
        return wav.repeat(channels, 1)
    return wav[:channels]


def build_prompt(base_prompt, instruction):
    """Combina el prompt original de la pista amb les noves instruccions de l'usuari."""
    parts = [p.strip() for p in (base_prompt, instruction) if p and p.strip()]
    return ". ".join(parts) if parts else "music"


def generate_candidate(model_obj, use_melody, base_wav, sr, prompt, seconds):
    """Genera una candidata completa de `seconds` segons, condicionada a l'àudio base si el model ho permet."""
    model_obj.set_generation_params(duration=seconds)
    if use_melody:
        out = model_obj.generate_with_chroma([prompt], base_wav[None], sr)
    else:
        out = model_obj.generate([prompt])
    return out[0].cpu()


def apply_regenerate(model_obj, use_melody, base_wav, sr, base_prompt, instruction):
    """Regenera la cançó completa a partir de la referència i de les noves instruccions."""
    seconds = min(MAX_GENERATION_SECONDS, max(1, round(base_wav.shape[-1] / sr)))
    return generate_candidate(model_obj, use_melody, base_wav, sr, build_prompt(base_prompt, instruction), seconds)


def apply_modify_regions(model_obj, use_melody, base_wav, sr, base_prompt, annotations):
    """Substitueix només les regions indicades per una candidata nova.

    Totes les regions es validen abans d'escriure res. Si una regió no existeix
    completament a la candidata, es llança un error i no es modifica el resultat.
    No s'aplica crossfade: els canvis són directes als punts d'unió.
    """
    seconds = min(MAX_GENERATION_SECONDS, max(1, round(base_wav.shape[-1] / sr)))
    annotation_text = "; ".join(
        f"from {a['startTime']:.1f}s to {a['endTime']:.1f}s: {a['instruction']}" for a in annotations
    )
    candidate = generate_candidate(model_obj, use_melody, base_wav, sr,
                                   build_prompt(base_prompt, annotation_text), seconds)
    candidate = match_channels(candidate, base_wav.shape[0])

    spans = []
    for a in annotations:
        start = int(round(a['startTime'] * sr))
        end = int(round(a['endTime'] * sr))
        if end > base_wav.shape[-1] or end > candidate.shape[-1]:
            raise ValueError("Una regió no existeix completament al resultat; no s'ha modificat res")
        spans.append((start, end))

    result = base_wav.clone()
    for start, end in spans:
        result[..., start:end] = candidate[..., start:end]
    return result


def apply_extend(model_obj, base_wav, sr, base_prompt, seconds, instruction):
    """Allarga el final de la cançó usant els darrers segons com a context.

    La part del context que retorna MusicGen es descarta; només s'afegeix la
    continuació nova. No s'afegeix crossfade.
    """
    context_len = min(base_wav.shape[-1], int(10 * sr))
    context = base_wav[..., -context_len:]
    model_obj.set_generation_params(duration=seconds)
    out = model_obj.generate_continuation(context[None], sr, descriptions=[build_prompt(base_prompt, instruction)])
    continuation = out[0].cpu()
    extra_len = int(round(seconds * sr))
    tail = match_channels(continuation[..., -extra_len:], base_wav.shape[0])
    if tail.shape[-1] < extra_len * 0.9:
        raise RuntimeError("MusicGen no ha generat la continuació completa")
    return torch.cat([base_wav, tail], dim=-1)


def run_edit(revision_id):
    """Executa una operació d'edició en segon pla i crea la revisió corresponent.

    La revisió només passa a ser activa quan el seu fitxer s'ha creat correctament.
    En cas d'error, la versió activa no canvia.

    Args:
        revision_id: identificador de la revisió pendent.
    """
    rev = db.session.get(TrackRevision, revision_id)
    if not rev:
        return
    session_id = rev.session_id
    session = db.session.get(EditSession, session_id)
    track = db.session.get(Track, session.track_id)
    params = json.loads(rev.params or '{}')
    try:
        rev.status = 'generating'
        db.session.commit()

        base_wav, sr = torchaudio.load(revision_base_path(track, rev))
        active_model = get_model(track.model_name)
        use_melody = 'melody' in track.model_name.lower()

        if rev.operation == 'regenerate':
            new_wav = apply_regenerate(active_model, use_melody, base_wav, sr, track.prompt, rev.instruction)
        elif rev.operation == 'modify':
            new_wav = apply_modify_regions(active_model, use_melody, base_wav, sr, track.prompt, params['annotations'])
        elif rev.operation == 'extend':
            new_wav = apply_extend(active_model, base_wav, sr, track.prompt, params['seconds'], rev.instruction)
        else:
            raise ValueError(f"Operació desconeguda: {rev.operation}")

        out_path = os.path.join(os.path.dirname(track.filepath), f"rev_{rev.id}.wav")
        temp_path = out_path + ".tmp.wav"
        torchaudio.save(temp_path, new_wav, sr)
        os.replace(temp_path, out_path)

        rev.filepath = out_path
        rev.status = 'done'
        undo = load_stack(session.undo_stack)
        undo.append(session.active_revision_id)
        session.undo_stack = json.dumps(undo)
        session.redo_stack = '[]'
        session.active_revision_id = rev.id
    except Exception as e:
        db.session.rollback()
        failed = db.session.get(TrackRevision, revision_id)
        if failed:
            failed.status = 'error'
            failed.error_msg = str(e)
    finally:
        session = db.session.get(EditSession, session_id)
        if session:
            session.busy = False
        db.session.commit()


def edit_precheck(track):
    """Valida que una pista pot editar-se. Retorna (missatge d'error, codi HTTP) o None."""
    if track.status != 'done' or not track.filepath:
        return "La pista ha d'estar completada per poder editar-la", 400
    session = get_edit_session(track)
    if session and session.busy:
        return "Ja hi ha una operació d'edició en curs", 409
    if not os.path.exists(active_audio_path(track, session)):
        return "No s'ha trobat el fitxer d'àudio de la versió activa", 400
    return None


def start_edit(track, operation, instruction=None, params=None):
    """Crea una revisió pendent amb pare la versió activa i l'encua per a execució."""
    session = get_edit_session(track, create=True)
    rev = TrackRevision(session_id=session.id, parent_id=session.active_revision_id, operation=operation,
                        instruction=instruction, params=json.dumps(params or {}), status='pending')
    session.busy = True
    db.session.add(rev)
    db.session.commit()
    task_queue.put(('edit', rev.id))
    return rev


def edit_state(track):
    """Retorna l'estat complet de l'editor d'una pista: versió activa, historial i waveform."""
    session = get_edit_session(track)
    active_path = active_audio_path(track, session)
    revisions = []
    if session:
        for rev in sorted(session.revisions, key=lambda r: r.created_at):
            revisions.append({
                'id': rev.id, 'parent_id': rev.parent_id, 'operation': rev.operation,
                'instruction': rev.instruction, 'status': rev.status, 'error_msg': rev.error_msg,
                'created_at': rev.created_at.isoformat(),
                'is_active': rev.id == session.active_revision_id,
            })
    return {
        'track_id': track.id,
        'active_revision_id': session.active_revision_id if session else None,
        'busy': bool(session and session.busy),
        'can_undo': bool(session and load_stack(session.undo_stack)),
        'can_redo': bool(session and load_stack(session.redo_stack)),
        'revisions': revisions,
        'active_url': to_web_path(active_path),
        'duration': round(audio_duration(active_path), 3),
        'peaks': compute_peaks(active_path),
        'max_generation_seconds': MAX_GENERATION_SECONDS,
        'warnings': {'experimental': EXPERIMENTAL_WARNING, 'regenerate': REGENERATE_WARNING},
    }


@app.route("/api/tracks/<track_id>/edit", methods=["GET"])
def get_track_edit_state(track_id):
    """Retorna l'estat de l'editor d'una pista per a la vista d'edició."""
    track = db.session.get(Track, track_id)
    if not track or not track.filepath:
        return jsonify({"error": "Not found"}), 404
    return jsonify(edit_state(track))


@app.route("/api/tracks/<track_id>/edit/regenerate", methods=["POST"])
def edit_regenerate(track_id):
    """Encua la regeneració completa de la cançó amb noves instruccions."""
    track = db.session.get(Track, track_id)
    if not track:
        return jsonify({"error": "Not found"}), 404
    error = edit_precheck(track)
    if error:
        return jsonify({"error": error[0]}), error[1]
    instruction = ((request.json or {}).get('instruction') or '').strip()
    if not instruction:
        return jsonify({"error": "Cal indicar què vols canviar"}), 400
    start_edit(track, 'regenerate', instruction=instruction)
    return jsonify({"success": True, "state": edit_state(track)})


@app.route("/api/tracks/<track_id>/edit/modify", methods=["POST"])
def edit_modify(track_id):
    """Encua la modificació de regions (experimental). Cada anotació té startTime, endTime i instruction."""
    track = db.session.get(Track, track_id)
    if not track:
        return jsonify({"error": "Not found"}), 404
    error = edit_precheck(track)
    if error:
        return jsonify({"error": error[0]}), error[1]
    raw = (request.json or {}).get('annotations') or []
    if not raw:
        return jsonify({"error": "Cal seleccionar almenys una regió"}), 400

    session = get_edit_session(track)
    total = audio_duration(active_audio_path(track, session))
    annotations = []
    try:
        for item in raw:
            start = float(item['startTime'])
            end = float(item['endTime'])
            instruction = (item.get('instruction') or '').strip()
            if not instruction:
                return jsonify({"error": "Cada regió necessita una instrucció"}), 400
            if start < 0 or end > total + 0.01 or end - start < 0.5:
                return jsonify({"error": "Les regions han d'estar dins la cançó i durar almenys 0,5 s"}), 400
            annotations.append({'startTime': start, 'endTime': end, 'instruction': instruction})
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Format d'anotacions no vàlid"}), 400
    annotations.sort(key=lambda a: a['startTime'])
    for prev, nxt in zip(annotations, annotations[1:]):
        if nxt['startTime'] < prev['endTime']:
            return jsonify({"error": "Les regions no es poden solapar"}), 400

    start_edit(track, 'modify', params={'annotations': annotations})
    return jsonify({"success": True, "state": edit_state(track)})


@app.route("/api/tracks/<track_id>/edit/extend", methods=["POST"])
def edit_extend(track_id):
    """Encua l'allargament de la cançó pel final, amb una durada en segons."""
    track = db.session.get(Track, track_id)
    if not track:
        return jsonify({"error": "Not found"}), 404
    error = edit_precheck(track)
    if error:
        return jsonify({"error": error[0]}), error[1]
    data = request.json or {}
    try:
        seconds = int(data.get('seconds', 0))
    except (TypeError, ValueError):
        return jsonify({"error": "Durada no vàlida"}), 400
    if not 1 <= seconds <= MAX_GENERATION_SECONDS:
        return jsonify({"error": f"La durada ha d'estar entre 1 i {MAX_GENERATION_SECONDS} segons"}), 400
    start_edit(track, 'extend', instruction=(data.get('instruction') or '').strip(), params={'seconds': seconds})
    return jsonify({"success": True, "state": edit_state(track)})


@app.route("/api/tracks/<track_id>/edit/undo", methods=["POST"])
def edit_undo(track_id):
    """Torna a la versió anterior sense eliminar cap revisió."""
    track = db.session.get(Track, track_id)
    session = get_edit_session(track) if track else None
    if not session:
        return jsonify({"error": "No hi ha cap edició oberta"}), 400
    if session.busy:
        return jsonify({"error": "Ja hi ha una operació d'edició en curs"}), 409
    undo = load_stack(session.undo_stack)
    if not undo:
        return jsonify({"error": "No hi ha res per desfer"}), 400
    redo = load_stack(session.redo_stack)
    redo.append(session.active_revision_id)
    session.active_revision_id = undo.pop()
    session.undo_stack = json.dumps(undo)
    session.redo_stack = json.dumps(redo)
    db.session.commit()
    return jsonify({"success": True, "state": edit_state(track)})


@app.route("/api/tracks/<track_id>/edit/redo", methods=["POST"])
def edit_redo(track_id):
    """Reavança a la versió desfeta més recentment."""
    track = db.session.get(Track, track_id)
    session = get_edit_session(track) if track else None
    if not session:
        return jsonify({"error": "No hi ha cap edició oberta"}), 400
    if session.busy:
        return jsonify({"error": "Ja hi ha una operació d'edició en curs"}), 409
    redo = load_stack(session.redo_stack)
    if not redo:
        return jsonify({"error": "No hi ha res per refer"}), 400
    undo = load_stack(session.undo_stack)
    undo.append(session.active_revision_id)
    session.active_revision_id = redo.pop()
    session.undo_stack = json.dumps(undo)
    session.redo_stack = json.dumps(redo)
    db.session.commit()
    return jsonify({"success": True, "state": edit_state(track)})


@app.route("/api/tracks/<track_id>/edit/confirm", methods=["POST"])
def edit_confirm(track_id):
    """Confirma la versió activa: substitueix l'original i elimina la resta de revisions i l'historial."""
    track = db.session.get(Track, track_id)
    session = get_edit_session(track) if track else None
    if not session:
        return jsonify({"error": "No hi ha cap edició oberta"}), 400
    if session.busy:
        return jsonify({"error": "Ja hi ha una operació d'edició en curs"}), 409

    if session.active_revision_id:
        rev = db.session.get(TrackRevision, session.active_revision_id)
        if not rev or rev.status != 'done' or not rev.filepath:
            return jsonify({"error": "La versió activa no és vàlida"}), 400
        os.replace(rev.filepath, track.filepath)
        album_name = track.album.title if track.album else "Singles"
        write_metadata(track.filepath, track.title, track.artist, album_name)
        remove_cached_exports(track)
    for other in session.revisions:
        if other.filepath and other.filepath != track.filepath:
            remove_file(other.filepath)
    db.session.delete(session)
    db.session.commit()
    return jsonify({"success": True, "track": track.to_dict()})


@app.route("/api/tracks/<track_id>/edit/cancel", methods=["POST"])
def edit_cancel(track_id):
    """Cancel·la l'edició: elimina les revisions i l'historial, i deixa l'original intacte."""
    track = db.session.get(Track, track_id)
    session = get_edit_session(track) if track else None
    if session and session.busy:
        return jsonify({"error": "Espera que acabi l'operació en curs abans de cancel·lar"}), 409
    if track:
        discard_edit_session(track)
    return jsonify({"success": True})


# --- COMFYUI STARTUP ---
def start_comfyui():
    """Clona, prepara i arrenca ComfyUI en segon pla si encara no és disponible."""
    if os.environ.get("ENABLE_COMFYUI") != "1" and not os.path.exists("/opt/ComfyUI"):
        return
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
        subprocess.run(["pip", "install", "-r", f"{COMFY_DIR}/requirements.txt"])

    import sys
    env = os.environ.copy()

    print("Iniciando ComfyUI en el puerto 8188...")
    extra_yaml = os.path.join(COMFY_DIR, "extra_model_paths.yaml")
    with open(extra_yaml, "w") as f:
        f.write(f"musicgen:\n    base_path: {os.path.abspath('comfyui_data')}\n    checkpoints: models/checkpoints")

    subprocess.Popen([sys.executable, "main.py", "--listen", "0.0.0.0", "--extra-model-paths-config", extra_yaml], cwd=COMFY_DIR, env=env)


# --- ACE-STEP 1.5 STARTUP ---
def start_acestep():
    """Arrenca el servidor REST d'ACE-Step 1.5 en segon pla al port 8001 si és disponible."""
    acestep_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "acestep_service")
    if not os.path.exists(acestep_dir):
        return

    candidate_pythons = [
        "/opt/acestep_env/bin/python",
        "/opt/conda/envs/acestep/bin/python",
        os.path.join(acestep_dir, ".venv", "bin", "python"),
        os.path.join(acestep_dir, ".venv", "Scripts", "python.exe"),
    ]
    python_bin = next((p for p in candidate_pythons if os.path.exists(p)), None)
    if not python_bin:
        print("[ACE-Step] No s'ha trobat l'entorn de Python per a ACE-Step. S'omet l'arrencada automàtica.")
        return

    try:
        r = requests.get("http://127.0.0.1:8001/health", timeout=1)
        if r.status_code == 200:
            print("[ACE-Step] El servidor al port 8001 ja està en marxa.")
            return
    except Exception:
        pass

    print(f"[ACE-Step] Iniciant el servidor REST al port 8001 utilitzant {python_bin}...")
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{acestep_dir}:{env.get('PYTHONPATH', '')}"
    cmd = [
        python_bin, "-m", "acestep.api_server",
        "--host", "0.0.0.0",
        "--port", "8001",
        "--lm-model-path", "acestep-5Hz-lm-0.6B",
        "--no-init"
    ]
    subprocess.Popen(cmd, cwd=acestep_dir, env=env)


threading.Thread(target=start_acestep, daemon=True).start()
threading.Thread(target=start_comfyui, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=False)
