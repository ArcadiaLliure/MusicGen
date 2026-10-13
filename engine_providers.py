import os
import time
import json
import gc
import urllib.request
import urllib.parse
import requests
from abc import ABC, abstractmethod
import torch
import torchaudio
from mutagen.wave import WAVE
import mutagen.id3 as id3

ACESTEP_DEFAULT_URL = os.environ.get("ACESTEP_API_URL", "http://127.0.0.1:8001")
YUE_DEFAULT_URL = os.environ.get("YUE_API_URL", "http://127.0.0.1:8791")

# Mapeig acústic d'instruments per a prompts enriquits (anglès d'alta fidelitat per a IA)
INSTRUMENT_ACOUSTIC_PROMPTS = {
    # Originals
    "Piano": "acoustic grand piano with rich dynamic resonance",
    "Clavicord": "clavichord with delicate expressive vibrato keyboard timbre",
    "Synth": "analog synthesizer with warm pads and melodic leads",
    "Acoustic Guitar": "acoustic steel-string guitar with warm fingerpicking",
    "Spanish Guitar": "classical Spanish nylon-string guitar with resonant rasgueado",
    "Elec Guitar": "electric guitar with articulate clean and overdriven tones",
    "Bass": "electric bass guitar with punchy deep low-end groove",
    "Ukulele": "acoustic soprano ukulele with bright cheerful strumming",
    "Harp": "concert pedal harp with delicate shimmering arpeggios",
    "Contrabass": "acoustic double bass with deep bowed contrabass warmth",
    "Cello": "expressive acoustic cello with warm emotional bowing",
    "Violin": "acoustic violin with singing virtuosic melodic phrasing",
    "Flute": "concert western flute with agile airy woody breath",
    "Clarinet": "acoustic clarinet with smooth wooden melodic tone",
    "Oboe": "acoustic oboe with poignant reedy double-reed timbre",
    "Fagot": "orchestral bassoon with woody low double-reed register",
    "Gralla": "traditional Catalan gralla with powerful piercing double reed",
    "Saxophone": "expressive saxophone with warm brassy reedy voice",
    "Trumpet": "brass trumpet with triumphant brilliant melodic fanfare",
    "Trombone": "tenor trombone with majestic warm brass slide harmonics",
    "Harmonica": "blues harmonica with soulful acoustic reed bends",
    "Drums": "full acoustic drum kit with dynamic kick, snare and hi-hat groove",
    "Choir": "mixed choir chorus with rich polyphonic harmonies",
    # Vocal Master & Extensions
    "Voice": "expressive lead vocals, clear vocal delivery",
    "Gregorian Chant": "monastic Latin Gregorian plainchant with reverberant sacred cathedral acoustics",
    "Byzantine Chant": "Byzantine liturgical chant with microtonal Greek psalmody and deep ison drone",
    "Male Choir": "deep male choir with resonant baritone and bass registers",
    "Female Choir": "ethereal female choir with soaring soprano and alto vocal harmonies",
    "Solo Voice": "intimate acoustic solo vocal melody",
    # Antiga Roma
    "Roman Tibia": "ancient Roman tibia double-pipe reed woodwind with piercing archaic timbre",
    "Roman Lyre": "ancient Roman lyra with plucked gut strings and wooden soundbox",
    "Roman Kithara": "noble Roman concert kithara with resonant wooden string box",
    "Cornu": "ancient Roman cornu circular bronze military horn with deep commanding calls",
    "Buccina": "Roman buccina curved brass military horn",
    "Roman Tuba": "ancient Roman straight bronze military trumpet tuba",
    "Lituus": "ancient Roman lituus bronze curved-bell ritual horn",
    "Hydraulis": "ancient Roman water organ hydraulis with flute-like water-pressured organ pipes",
    "Sistrum": "ancient ceremonial bronze sistrum metallic rattle",
    "Ancient Cymbals": "ancient bronze finger cymbals with bright ringing metallic resonance",
    "Crotales": "ancient tuned bronze and wood crotales clappers",
    "Scabellum": "Roman scabellum wooden foot clapper percussive theatrical pulse",
    "Pan Flute": "ancient pan flute syrinx with breathy rustic multi-pipe melodies",
    "Pandura": "ancient long-necked plucked lute pandura",
    "Roman Tympanum": "ancient Roman tympanum hand drum with resonant skin timbre",
    # Antiga Grècia
    "Greek Kithara": "ancient Greek concert kithara plucked string instrument",
    "Greek Lyre": "ancient Greek tortoise-shell lyre with sweet delicate gut strings",
    "Greek Aulos": "ancient Greek double-reed aulos pipes with intense modal microtonal melody",
    "Barbitos": "ancient Greek barbitos long-armed bass lyre with deep sonorous strings",
    "Phorminx": "Homeric archaic phorminx crescent lyre",
    "Salpinx": "ancient Greek straight bronze heraldic trumpet salpinx",
    "Greek Tympanon": "ancient Greek Dionysian frame drum tympanon",
    # Bizanci
    "Byzantine Lyra": "Byzantine pear-shaped bowed lyra with rich melodic drones",
    "Byzantine Psaltery": "Byzantine plucked metal-string psaltery zither",
    "Liturgical Bells": "Eastern Orthodox church bells with deep harmonic chime resonance",
    "Byzantine Organ": "Byzantine imperial pneumatic pipe organ",
    "Def": "def frame drum with bronze jingles",
    # Medieval
    "Medieval Lute": "medieval plectrum lute with bright articulate gut strings",
    "Medieval Vihuela": "medieval vihuela with historical aristocratic timbre",
    "Gittern": "medieval carved wooden gittern lute with quill plectrum",
    "Citole": "medieval citole plucked string instrument",
    "Medieval Harp": "gothic medieval harp with bray pins and buzzing crystalline timbre",
    "Medieval Psaltery": "medieval pig's head psaltery with bell-like plucked strings",
    "Rebec": "medieval bowed rebec with sharp piercing rustic voice",
    "Vielle": "medieval vielle fiddle with flat bridge and sustained drone strings",
    "Organistrum": "medieval organistrum large keyed wheel instrument",
    "Hurdy-gurdy": "medieval hurdy-gurdy zanfona with buzzing drone wheel and keyed strings",
    "Portative Organ": "medieval portative organetto with handheld bellows and flute pipes",
    "Positive Organ": "chamber positive organ with sweet wooden pipe stops",
    "Medieval Recorder": "medieval cylindrical wooden recorder with pure breathy flute tone",
    "Pipe and Tabor": "medieval three-hole pipe whistle and tabor drum played together",
    "Shawm": "medieval shawm double reed with fiery loud outdoor reedy timbre",
    "Bombard": "Breton and medieval bombard with deep powerful double-reed punch",
    "Medieval Bagpipe": "medieval leather bagpipe with cane chanter and bass drone",
    "Anafil": "straight Moorish and medieval brass trumpet anafil",
    "Natural Horn": "medieval natural animal horn call",
    "Tabor": "medieval tabor rope-tension drum with gut snare",
    "Nakers": "medieval paired kettle drums nakers",
    "Medieval Chimes": "medieval tintinnabulum chime bells with high metallic ring",
    "Dulcimer": "hammered dulcimer with wooden mallets striking brass strings",
    # Renaixement i Barroc
    "Harpsichord": "two-manual baroque harpsichord with crisp plucking quill keyboard counterpoint",
    "Virginal": "renaissance virginal keyboard with sweet resonant box timbre",
    "Theorbo": "baroque theorbo extended-neck archlute with deep diapason gut bass strings",
    "Viola da Gamba": "six-string fretted viola da gamba with warm silvery bowed consort timbre",
    "Cornett": "wooden leather-bound cornett zink with singing human-like brass tone",
    "Sackbut": "renaissance sackbut early trombone with mellow blendable brass slide",
    "Crumhorn": "capped-reed crumhorn with buzzy nasal consort wind",
    "Dulcian": "renaissance dulcian early bassoon with soft wooden low register",
    "Baroque Organ": "baroque pipe organ with grand polyphonic mixtures and reeds",
    "Natural Trumpet": "valveless baroque natural trumpet with brilliant clarino register",
    # Tradicional Català i Ibèric
    "Tenora": "Catalan cobla tenora oboe with majestic resonant metallic-belled double reed",
    "Tible": "Catalan tible treble shawm with bright festive melody",
    "Flabiol": "Catalan flabiol one-handed flute and tamborí drum",
    "Sac de Gemecs": "Catalan sac de gemecs bagpipe with three hanging bass drones",
    "Xeremia": "Majorcan xeremia bagpipe with lively Mediterranean dance tone",
    "Dolsaina": "Valencian dolçaina traditional shawm with intense festival melody",
    "Tarota": "rustic wooden tarota shawm with deep archaic double reed timbre",
    "Alboka": "Basque alboka double hornpipe with continuous circular-breathed drone",
    "Txistu": "Basque txistu three-hole pipe flute",
    "Trikitixa": "diatonic button accordion trikitixa with energetic folk rhythms",
    "Gaita Gallega": "Galician gaita bagpipe with rich harmonic drone and lyrical ornaments",
    "Gaita Asturiana": "Asturian gaita bagpipe with powerful loud drone and bright chanter",
    # Celta
    "Bodhran": "Irish bodhrán frame drum with tipper-struck rhythmic pulse",
    "Tin Whistle": "Irish tin penny whistle with sweet airy rapid jigs",
    "Low Whistle": "low D Irish whistle with deep haunting breathy air",
    "Uilleann Pipes": "Irish uilleann pipes with bellows-blown chanter, regulators and drones",
    "Irish Bouzouki": "Irish bouzouki with eight-string ringing open-chord accompaniment",
    "Nyckelharpa": "Swedish nyckelharpa keyed fiddle with shimmering sympathetic strings",
    "Hardanger Fiddle": "Norwegian Hardanger fiddle with decorated sympathetic resonance",
    "Kantele": "Finnish plucked kantele zither with bell-like acoustic purity",
    # Món
    "Oud": "fretless wooden oud with microtonal ornaments and warm plucking",
    "Qanun": "Middle Eastern qanun zither with rapid tremolos and metallic levers",
    "Ney": "end-blown reed flute ney with breathy meditative Sufi microtones",
    "Duduk": "Armenian apricot-wood duduk double-reed flute with mournful warm soul timbre",
    "Zurna": "outdoor double-reed zurna with fiery celebratory folk tone",
    "Saz": "long-necked saz baglama with tied microtonal frets and drone strings",
    "Santur": "Persian hammered santur with delicate mesrap strikes and glittering sustain",
    "Kamancheh": "Persian bowed spike fiddle kamancheh with silky microtones",
    "Darbuka": "goblet darbuka doumbek with sharp doum and tak accents",
    "Riq": "Arabic riq tambourine with heavy brass jingles and finger rolls",
    "Bendir": "North African bendir frame drum with buzzing snare cord resonance",
    "Sitar": "Indian classical sitar with jawari buzzing bridge and meend note bends",
    "Sarod": "fretless steel-fingerboard sarod with percussive coconut plectrum",
    "Tanpura": "Indian tanpura continuous hypnotic acoustic overtone drone foundation",
    "Bansuri": "Indian bamboo bansuri flute with lyrical glides and warm spiritual melodies",
    "Tabla": "paired Indian tabla drums with daya ring and baya bass pitch bends",
    "Sarangi": "Indian bowed sarangi with vocal-like sliding melodies",
    "Erhu": "Chinese two-string bowed erhu with crying vibrato",
    "Pipa": "Chinese pear-shaped pipa lute with rapid finger rolls and dramatic attacks",
    "Guzheng": "Chinese 21-string plucked guzheng zither with cascading water glissandos",
    "Dizi": "Chinese transverse bamboo dizi flute with buzzing dimo membrane",
    "Koto": "Japanese 13-string koto zither with elegant pentatonic plucks",
    "Shakuhachi": "Japanese end-blown bamboo shakuhachi with breathy meditative bends",
    "Shamisen": "Japanese three-string shamisen with percussive bachi plectrum strikes",
    "Taiko": "Japanese large taiko drums with thunderous dynamic ensemble power",
    "Kora": "West African 21-string harp-lute kora with intricate polyrhythmic arpeggios",
    "Mbira": "African mbira kalimba thumb piano with buzzy metallic resonance",
    "Balafon": "wooden balafon marimba with gourd resonators and bright melodic percussion",
    "Djembe": "West African djembe drum with resonant bass and sharp slap",
    "Charango": "Andean charango with rapid high-pitched double-strum rasgueos",
    "Quena": "traditional Andean notched quena flute with woody breathy melodies",
    "Zampona": "Andean panpipe zampoña siku with airy cane pipes",
    "Cajon": "wooden cajón box drum with punchy bass and snappy snare slap",
    # Moderns
    "Viola": "orchestral viola with warm dark mellow bowed string voice",
    "Piccolo": "orchestral piccolo with brilliant sparkling high register",
    "English Horn": "cor anglais tenor oboe with melancholy lyrical double reed",
    "Bass Clarinet": "bass clarinet with velvety deep low-register woodwind warmth",
    "French Horn": "French horn with noble mellow brass calls and soaring anthems",
    "Modern Tuba": "orchestral brass tuba with foundational low-end weight",
    "Timpani": "orchestral kettle drums timpani with dramatic tuned thunder",
    "Glockenspiel": "orchestral glockenspiel with bright crystalline steel bells",
    "Xylophone": "acoustic xylophone with dry snappy wooden mallets",
    "Marimba": "concert marimba with warm deep velvety wooden bars",
    "Vibraphone": "jazz vibraphone with motorized tremolo fans and warm metallic sustain",
    "Celesta": "orchestral celesta keyboard with bell-like magical timbre",
    "Gong": "orchestral tam-tam gong with colossal crashing wash and deep decay",
    "Hammond Organ": "Hammond B3 tonewheel organ with Leslie rotating speaker swirl",
    "Mellotron": "vintage tape-replay Mellotron with nostalgic lo-fi flute and strings"
}

STYLE_DESCRIPTORS = {
    "ancient_rome": "authentic ancient Roman music, classical antiquities, modal Greco-Roman scales, ritual and martial atmosphere",
    "ancient_greece": "ancient Greek music, Pythagorean tuning, ancient modal harmoniai, lyrical and philosophical character",
    "byzantine": "Byzantine chant and imperial court music, sacred Eastern Orthodox modal scales, liturgical solemnity",
    "monastic_gregorian": "monastic Gregorian plainchant, sacred Latin liturgical tradition, quiet contemplative reverberant abbey",
    "medieval_european": "medieval European music, troubadour and trouvère melodies, courtly love, gothic polyphony",
    "medieval_fantasy": "epic medieval fantasy soundtrack, mystical ancient atmosphere, adventurous acoustic orchestration",
    "renaissance": "European Renaissance music, vocal and instrumental consort polyphony, elegant dance forms",
    "baroque": "European Baroque music, basso continuo, counterpoint and ornate melodic decoration",
    "classical": "Classical era music, balanced orchestral harmonies, expressive phrasing, sonata form character",
    "romanticism": "19th century Romantic era music, profound emotional intensity, virtuosic orchestral and piano texture",
    "orchestral": "full symphonic orchestra, cinematic grandeur, sweeping strings, noble brass and dynamic woodwinds",
    "cinematic": "cinematic film score, atmospheric hybrid orchestration, high emotional resonance and drama",
    "celtic": "traditional Celtic and Nordic folk music, reels, jigs and evocative airs with ancient resonance",
    "catalan_trad": "música tradicional catalana, cobla sonorities, Mediterranean folk melodies and festivity",
    "iberian_folk": "Iberian traditional folk music, rustic roots, ancestral dances and rhythms",
    "andalusi": "música araboandalusí, medieval Al-Andalus classical nubah, Mediterranean modal elegance",
    "traditional_arabic": "traditional Arabic maqam music, microtonal ornamentation, taqsim improvisations",
    "persian": "classical Persian radif music, dastgah modal framework, mystical lyrical soul",
    "indian_classical": "Indian classical music, meditative raga development, hypnotic tala rhythmic cycles",
    "chinese_trad": "traditional Chinese silk and bamboo music, pentatonic elegance, nature-inspired poetry",
    "japanese_trad": "traditional Japanese music, Ma aesthetic space, Zen restraint and dramatic dynamics",
    "african_trad": "traditional West African music, complex polyrhythms, griot storytelling traditions",
    "latin_american": "traditional Andean and Latin American folklore, mountain airs, rhythmic acoustic vibrancy",
    "sacred_choral": "sacred choral music, solemn cathedral acoustics, uplifting vocal polyphony",
    "jazz": "acoustic jazz, swinging groove, sophisticated harmonic changes, expressive improvisation",
    "blues": "authentic acoustic blues, expressive bends, soulful groove",
    "rock": "rock music with driving drums, bass and electric energy",
    "pop": "modern pop music production, polished melodic hooks",
    "electronic": "electronic music with rich synthesizer soundscapes and rhythmic pulse",
    "ambient": "ambient music, expansive meditative soundscapes, tranquil textures",
    "contemporary_folk": "contemporary acoustic folk, heartfelt songwriting, organic acoustic instrumentation"
}


def compile_prompt(base_prompt, instrument_states=None, selected_style="all"):
    """
    Construeix un prompt musical acuradament integrat i enriquits amb descriptors
    acústics segons els instruments obligatoris, opcionals i prohibits, i l'estil seleccionat.
    """
    parts = []

    # 1. Estil musical si està definit
    if selected_style and selected_style != "all" and selected_style in STYLE_DESCRIPTORS:
        parts.append(STYLE_DESCRIPTORS[selected_style] + ".")

    # 2. Parseig d'instruments
    states = {}
    if isinstance(instrument_states, str) and instrument_states:
        try:
            states = json.loads(instrument_states)
        except Exception:
            states = {}
    elif isinstance(instrument_states, dict):
        states = instrument_states

    required_desc = []
    optional_desc = []
    forbid_names = []

    for inst_id, st in states.items():
        desc = INSTRUMENT_ACOUSTIC_PROMPTS.get(inst_id, inst_id)
        if st == 1:
            required_desc.append(desc)
        elif st == 2:
            optional_desc.append(desc)
        elif st == 3:
            forbid_names.append(inst_id)

    if required_desc:
        parts.append(f"Featured instruments: {', '.join(required_desc)}.")
    if optional_desc:
        parts.append(f"Optional accompaniment: {', '.join(optional_desc)}.")
    if forbid_names:
        parts.append(f"Strictly NO {', NO '.join(forbid_names)}.")

    # 3. Prompt de text de l'usuari (sense duplicar instruments repetits)
    clean_base = (base_prompt or "").strip()
    if clean_base:
        parts.append(clean_base)

    compiled = " ".join(parts).strip()
    return compiled or "High quality music composition"


class MusicGenerationProvider(ABC):
    """Interfície base comuna per als motors de generació musical."""

    @abstractmethod
    def generate(self, track, options=None):
        """Genera el fitxer d'àudio per a la pista indicada i retorna la ruta local del fitxer WAV."""
        pass

    @abstractmethod
    def unload(self):
        """Allibera la memòria VRAM utilitzada pel model per permetre l'ús de la GPU per un altre motor."""
        pass

    @abstractmethod
    def is_loaded(self):
        """Indica si el model està carregat a la GPU."""
        pass


class MusicGenProvider(MusicGenerationProvider):
    """Adaptador per a Meta AudioCraft / MusicGen in-process."""
    _instance = None

    def __init__(self, get_model_fn, library_dir="static/library"):
        self.get_model_fn = get_model_fn
        self.library_dir = library_dir
        self.active_model = None
        self.current_model_name = None
        MusicGenProvider._instance = self

    @classmethod
    def get_instance(cls):
        return cls._instance

    def is_loaded(self):
        return self.active_model is not None

    def unload(self):
        if self.active_model is not None:
            print("[MusicGenProvider] Descarregant model de MusicGen de la GPU...")
            del self.active_model
            self.active_model = None
            self.current_model_name = None
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            print("[MusicGenProvider] VRAM de MusicGen alliberada correctament.")

    def generate(self, track, options=None):
        try:
            from audiocraft.data.audio import audio_write
        except ImportError:
            raise RuntimeError("Meta AudioCraft (audiocraft) no està instal·lat en aquest entorn de Python.")

        options = options or {}
        model_name = track.model_name or "facebook/musicgen-melody"
        self.active_model = self.get_model_fn(model_name)
        self.current_model_name = model_name
        self.active_model.set_generation_params(duration=track.duration or 30)

        prompt_text = track.prompt
        reference_path = options.get("reference_path")

        if reference_path and 'melody' in model_name.lower():
            melody, sr = torchaudio.load(reference_path)
            wav = self.active_model.generate_with_chroma([prompt_text], melody[None], sr)
        else:
            wav = self.active_model.generate([prompt_text])

        album_dir = os.path.join(self.library_dir, track.album_id or "Singles")
        os.makedirs(album_dir, exist_ok=True)
        filename = f"{track.track_order:02d}_{track.title[:20].replace(' ', '_')}_{int(time.time())}"
        filepath_no_ext = os.path.join(album_dir, filename)
        audio_write(filepath_no_ext, wav[0].cpu(), self.active_model.sample_rate, strategy="loudness", loudness_compressor=True)
        final_filepath = filepath_no_ext + ".wav"

        album_name = track.album.title if (hasattr(track, 'album') and track.album) else "Singles"
        self._write_metadata(final_filepath, track.title, track.artist, album_name)
        return final_filepath

    def _write_metadata(self, filepath, title, artist, album):
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
            print(f"[MusicGenProvider] Error escrivint metadades: {e}")


class AceStepProvider(MusicGenerationProvider):
    """Adaptador asíncron per al servei REST d'ACE-Step 1.5."""

    def __init__(self, api_url=None, library_dir="static/library"):
        self.api_url = (api_url or ACESTEP_DEFAULT_URL).rstrip('/')
        self.library_dir = library_dir

    def is_loaded(self):
        # El servei d'ACE-Step corre com a procés/servei independent
        try:
            r = requests.get(f"{self.api_url}/health", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def unload(self):
        # Descarrega opcional dels pesos d'ACE-Step si suportat
        pass

    def check_health(self):
        """Comprova si el servidor ACE-Step està actiu i escoltant."""
        urls_to_try = [self.api_url]
        if "127.0.0.1" in self.api_url or "localhost" in self.api_url:
            urls_to_try.append(self.api_url.replace("127.0.0.1", "host.docker.internal").replace("localhost", "host.docker.internal"))
        for target in urls_to_try:
            try:
                r = requests.get(f"{target}/health", timeout=3)
                if r.status_code == 200:
                    self.api_url = target
                    return True
            except Exception:
                continue
        return False

    def generate(self, track, options=None):
        options = options or {}

        # 1. Comprova que el servidor d'ACE-Step estigui disponible
        if not self.check_health():
            raise RuntimeError(
                f"El servidor d'ACE-Step 1.5 no respon a {self.api_url}. "
                f"Assegura't que el servei estigui iniciat a la màquina o al port 8001."
            )

        # 2. Descarrega MusicGen de la VRAM abans de començar per garantir que la RTX 3060 tingui espai
        mg_prov = MusicGenProvider.get_instance()
        if mg_prov and mg_prov.is_loaded():
            mg_prov.unload()

        # 3. Prepara paràmetres d'inferència
        model_name = track.model_name or "acestep-v15-turbo"
        is_turbo = "turbo" in model_name.lower()
        inference_steps = 8 if is_turbo else 32

        # 4. Construeix el prompt acurat
        prompt_text = track.prompt
        lyrics_text = (track.lyrics or "").strip()

        # Si l'instrument «Voz» està prohibit als estats, assegura mode instrumental
        states = {}
        if track.instrument_states:
            try:
                states = json.loads(track.instrument_states) if isinstance(track.instrument_states, str) else track.instrument_states
            except Exception:
                pass
        if states.get("Voice") == 3:
            lyrics_text = ""

        duration = float(track.duration or 30)

        payload = {
            "prompt": prompt_text,
            "lyrics": lyrics_text,
            "audio_duration": duration,
            "model": model_name,
            "inference_steps": inference_steps,
            "thinking": bool(lyrics_text),
            "audio_format": "wav",
            "batch_size": 1,
            "use_random_seed": True
        }

        print(f"[AceStepProvider] Enviant tasca a ACE-Step ({model_name}, {duration}s, {inference_steps} passos)...")
        release_res = requests.post(f"{self.api_url}/release_task", json=payload, timeout=30)
        if release_res.status_code != 200:
            raise RuntimeError(f"Error en alliberar tasca a ACE-Step: {release_res.text}")

        res_json = release_res.json()
        task_id = (res_json.get("data") or {}).get("task_id")
        if not task_id:
            raise RuntimeError(f"No s'ha rebut task_id d'ACE-Step: {res_json}")

        print(f"[AceStepProvider] Tasca rebuda amb èxit: {task_id}. Monitoritzant progrés...")

        # 5. Enquesta asíncrona a /query_result
        poll_interval = 2
        max_timeout = 1800  # 30 minuts màxim (cobreix la descàrrega inicial dels pesos)
        elapsed = 0
        audio_url_path = None

        while elapsed < max_timeout:
            time.sleep(poll_interval)
            elapsed += poll_interval

            query_res = requests.post(f"{self.api_url}/query_result", json={"task_id_list": [task_id]}, timeout=15)
            if query_res.status_code != 200:
                continue

            q_data = query_res.json().get("data", [])
            if not q_data:
                continue

            task_info = q_data[0]
            status = task_info.get("status")

            if status == 1:
                # Tasca completada amb èxit!
                raw_result = task_info.get("result", "")
                result_obj = json.loads(raw_result) if isinstance(raw_result, str) else raw_result
                if isinstance(result_obj, list) and len(result_obj) > 0:
                    audio_url_path = result_obj[0].get("file")
                elif isinstance(result_obj, dict):
                    audio_url_path = result_obj.get("file")
                break
            elif status == 2:
                # Tasca fallida
                error_detail = task_info.get("result") or task_info.get("error") or "Error desconegut a ACE-Step"
                raise RuntimeError(f"Generació d'ACE-Step fallida: {error_detail}")

        if not audio_url_path:
            raise RuntimeError(f"Timeout o cap fitxer retornat per ACE-Step per a la tasca {task_id}")

        # 6. Descarrega el fitxer d'àudio
        download_url = f"{self.api_url}{audio_url_path}" if audio_url_path.startswith("/") else f"{self.api_url}/{audio_url_path}"
        print(f"[AceStepProvider] Descarregant àudio generat des de {download_url}...")

        audio_res = requests.get(download_url, timeout=60, stream=True)
        if audio_res.status_code != 200:
            raise RuntimeError(f"Error descarregant fitxer d'àudio d'ACE-Step: {audio_res.status_code}")

        album_dir = os.path.join(self.library_dir, track.album_id or "Singles")
        os.makedirs(album_dir, exist_ok=True)
        filename = f"{track.track_order:02d}_{track.title[:20].replace(' ', '_')}_{int(time.time())}.wav"
        final_filepath = os.path.join(album_dir, filename)

        with open(final_filepath, 'wb') as f:
            for chunk in audio_res.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # 7. Valida el fitxer descarregat
        if not os.path.exists(final_filepath) or os.path.getsize(final_filepath) < 1000:
            raise RuntimeError(f"El fitxer d'àudio generat és invàlid o buit: {final_filepath}")

        # 8. Escriu metadades ID3
        album_name = track.album.title if (hasattr(track, 'album') and track.album) else "Singles"
        self._write_metadata(final_filepath, track.title, track.artist, album_name)
        print(f"[AceStepProvider] Àudio generat i desat amb èxit a {final_filepath}")
        return final_filepath

    def _write_metadata(self, filepath, title, artist, album):
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
            print(f"[AceStepProvider] Error escrivint metadades: {e}")


def get_provider(model_name, get_model_fn=None, library_dir="static/library"):
    """Retorna el proveïdor de generació corresponent segons el model triat."""
    if model_name and (model_name.startswith("yue") or "yue" in model_name.lower()):
        return YuEProvider(library_dir=library_dir)
    elif model_name and model_name.startswith("acestep"):
        return AceStepProvider(library_dir=library_dir)
    else:
        return MusicGenProvider(get_model_fn=get_model_fn, library_dir=library_dir)


class YuEProvider(MusicGenerationProvider):
    """Adaptador per al servei de YuE2 (audiocpp_server en Linux Docker o YuE2 Studio)."""

    def __init__(self, api_url=None, library_dir="static/library"):
        self.api_url = (api_url or YUE_DEFAULT_URL).rstrip('/')
        self.library_dir = library_dir

    def is_loaded(self):
        try:
            r = requests.get(f"{self.api_url}/health", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def unload(self):
        pass

    def check_health(self):
        """Comprova si el servidor de YuE2 està actiu i escoltant."""
        urls_to_try = [self.api_url]
        if "yue2" in self.api_url:
            urls_to_try.extend(["http://127.0.0.1:8791", "http://localhost:8791"])
        if "127.0.0.1" in self.api_url or "localhost" in self.api_url:
            urls_to_try.extend([
                self.api_url.replace("127.0.0.1", "yue2").replace("localhost", "yue2"),
                self.api_url.replace("127.0.0.1", "host.docker.internal").replace("localhost", "host.docker.internal")
            ])
        for target in urls_to_try:
            try:
                r = requests.get(f"{target}/health", timeout=3)
                if r.status_code == 200:
                    self.api_url = target
                    return True
            except Exception:
                continue
        return False

    def generate(self, track, options=None):
        options = options or {}

        # 1. Comprova que el servidor de YuE2 estigui disponible
        if not self.check_health():
            raise RuntimeError(
                f"El servidor de YuE2 no respon a {self.api_url}. "
                f"Assegura't que el servei 'yue2' estigui en marxa a Docker o al port 8791."
            )

        # 2. Descarrega MusicGen de la VRAM abans de començar per garantir que la RTX 3060 tingui espai
        mg_prov = MusicGenProvider.get_instance()
        if mg_prov and mg_prov.is_loaded():
            mg_prov.unload()

        # 3. Prepara paràmetres d'inferència
        model_name = track.model_name or "yue2-3b"
        if "q4" in model_name.lower():
            target_model = "yue2-3b-q4"
        elif "q8" in model_name.lower():
            target_model = "yue2-3b-q8"
        else:
            target_model = "yue2-3b"

        # 4. Construeix el prompt acurat
        prompt_text = (track.prompt or "").strip()
        lyrics_text = (track.lyrics or "").strip()

        states = {}
        if track.instrument_states:
            try:
                states = json.loads(track.instrument_states) if isinstance(track.instrument_states, str) else track.instrument_states
            except Exception:
                pass
        if states.get("Voice") == 3:
            lyrics_text = ""
            if not prompt_text.lower().startswith("instrumental"):
                prompt_text = f"instrumental, {prompt_text}"

        duration = float(track.duration or 60)

        # 5. Execució via audiocpp_server (nadiu Docker Linux)
        audiocpp_payload = {
            "model": target_model,
            "options": {
                "style": prompt_text,
                "lyrics": lyrics_text,
                "cot": "full",
                "stop_after": "audio",
                "seed": int(time.time()) % 100000
            },
            "style": prompt_text,
            "lyrics": lyrics_text
        }

        print(f"[YuEProvider] Enviant tasca a YuE2 ({target_model}, {duration}s)...")
        task_res = None
        try:
            task_res = requests.post(f"{self.api_url}/v1/tasks/run", json=audiocpp_payload, timeout=1200)
        except Exception as e:
            print(f"[YuEProvider] Petició a /v1/tasks/run ha fallat: {e}")

        if task_res is not None:
            if task_res.status_code == 200:
                res_data = task_res.json()
                result = res_data.get("result") or {}
                audio_b64 = res_data.get("audio") or res_data.get("audio_base64")
                if not audio_b64 and isinstance(result, dict):
                    audio_b64 = result.get("audio_base64") or result.get("audio")
                audio_path = res_data.get("audio_path") or res_data.get("path")
                if not audio_path and isinstance(result, dict):
                    audio_path = result.get("audio_path") or result.get("path")

                album_dir = os.path.join(self.library_dir, track.album_id or "Singles")
                os.makedirs(album_dir, exist_ok=True)
                filename = f"{track.track_order:02d}_{track.title[:20].replace(' ', '_')}_{int(time.time())}.wav"
                final_filepath = os.path.join(album_dir, filename)

                if audio_b64:
                    import base64
                    if "," in audio_b64:
                        audio_b64 = audio_b64.split(",", 1)[1]
                    raw_audio = base64.b64decode(audio_b64)
                    with open(final_filepath, "wb") as f:
                        f.write(raw_audio)
                elif audio_path:
                    candidate_paths = [
                        audio_path,
                        os.path.join("static/library", os.path.basename(audio_path)),
                        os.path.join(self.library_dir, os.path.basename(audio_path)),
                        audio_path.replace("/app/output", self.library_dir),
                        os.path.join("/app/output", os.path.basename(audio_path))
                    ]
                    found = False
                    for p in candidate_paths:
                        if os.path.exists(p) and os.path.getsize(p) > 1000:
                            import shutil
                            shutil.copyfile(p, final_filepath)
                            found = True
                            break
                    if not found:
                        download_url = f"{self.api_url}/{audio_path.lstrip('/')}"
                        r_down = requests.get(download_url, timeout=30)
                        if r_down.status_code == 200:
                            with open(final_filepath, "wb") as f:
                                f.write(r_down.content)
                            found = True

                if os.path.exists(final_filepath) and os.path.getsize(final_filepath) > 1000:
                    album_name = track.album.title if (hasattr(track, 'album') and track.album) else "Singles"
                    self._write_metadata(final_filepath, track.title, track.artist, album_name)
                    print(f"[YuEProvider] Àudio generat i desat amb èxit a {final_filepath}")
                    return final_filepath
                else:
                    raise RuntimeError(f"YuE2 ha completat la tasca però no s'ha pogut guardar el fitxer d'àudio (res_keys={list(res_data.keys())})")
            elif task_res.status_code != 404 or "yue2" in self.api_url:
                raise RuntimeError(f"Error a YuE2 ({task_res.status_code}): {task_res.text}")

        # 6. Fallback a YuE2 Studio (Tauri API /v1/music/jobs)
        is_fast = "fast" in model_name.lower() or "turbo" in model_name.lower()
        solver = "ab2" if is_fast else "midpoint"
        payload = {
            "style": prompt_text,
            "lyrics": lyrics_text,
            "title": track.title or "Untitled",
            "duration_seconds": duration,
            "cot": "full",
            "solver": solver,
            "output_format": "flac"
        }

        print(f"[YuEProvider] Enviant tasca a YuE2 Studio ({model_name}, {duration}s, solver {solver})...")
        create_res = requests.post(f"{self.api_url}/v1/music/jobs", json=payload, timeout=30)
        if create_res.status_code not in (200, 201, 202):
            raise RuntimeError(f"Error en crear tasca a YuE2 ({create_res.status_code}): {create_res.text}")

        res_json = create_res.json()
        job_id = res_json.get("id")
        if not job_id:
            raise RuntimeError(f"No s'ha rebut id de feina de YuE2: {res_json}")

        print(f"[YuEProvider] Tasca creada amb èxit: {job_id}. Monitoritzant progrés...")

        poll_interval = 2
        max_timeout = 1800
        elapsed = 0
        song_id = None

        while elapsed < max_timeout:
            time.sleep(poll_interval)
            elapsed += poll_interval

            status_res = requests.get(f"{self.api_url}/v1/music/jobs/{job_id}", timeout=15)
            if status_res.status_code != 200:
                continue

            job_data = status_res.json()
            status = job_data.get("status")

            if status == "completed":
                songs = job_data.get("songs") or []
                if songs and isinstance(songs, list):
                    song_id = songs[0].get("id")
                elif job_data.get("song"):
                    song_id = (job_data.get("song") or {}).get("id")
                break
            elif status in ("failed", "cancelled"):
                error_detail = job_data.get("message") or job_data.get("error") or "Generació de YuE2 fallida"
                raise RuntimeError(f"Generació de YuE2 fallida ({status}): {error_detail}")

        if not song_id:
            raise RuntimeError(f"Timeout o cap pista retornada per YuE2 per a la tasca {job_id}")

        download_url = f"{self.api_url}/v1/library/media/{song_id}"
        print(f"[YuEProvider] Descarregant àudio generat des de {download_url}...")

        audio_res = requests.get(download_url, timeout=60, stream=True)
        if audio_res.status_code != 200:
            files_res = requests.get(f"{self.api_url}/v1/library/songs/{song_id}/files", timeout=15)
            if files_res.status_code == 200:
                audio_file_path = files_res.json().get("audio")
                if audio_file_path and os.path.exists(audio_file_path):
                    album_dir = os.path.join(self.library_dir, track.album_id or "Singles")
                    os.makedirs(album_dir, exist_ok=True)
                    filename = f"{track.track_order:02d}_{track.title[:20].replace(' ', '_')}_{int(time.time())}.wav"
                    final_filepath = os.path.join(album_dir, filename)
                    wav_data, sr = torchaudio.load(audio_file_path)
                    torchaudio.save(final_filepath, wav_data, sr)
                    album_name = track.album.title if (hasattr(track, 'album') and track.album) else "Singles"
                    self._write_metadata(final_filepath, track.title, track.artist, album_name)
                    return final_filepath

            raise RuntimeError(f"Error descarregant fitxer d'àudio de YuE2: {audio_res.status_code}")

        album_dir = os.path.join(self.library_dir, track.album_id or "Singles")
        os.makedirs(album_dir, exist_ok=True)
        temp_filename = f"{track.track_order:02d}_{track.title[:20].replace(' ', '_')}_{int(time.time())}.tmp"
        temp_filepath = os.path.join(album_dir, temp_filename)
        filename = f"{track.track_order:02d}_{track.title[:20].replace(' ', '_')}_{int(time.time())}.wav"
        final_filepath = os.path.join(album_dir, filename)

        with open(temp_filepath, 'wb') as f:
            for chunk in audio_res.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        if not os.path.exists(temp_filepath) or os.path.getsize(temp_filepath) < 1000:
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            raise RuntimeError(f"El fitxer d'àudio descarregat de YuE2 és invàlid o buit.")

        try:
            wav_data, sr = torchaudio.load(temp_filepath)
            torchaudio.save(final_filepath, wav_data, sr)
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
        except Exception:
            if os.path.exists(final_filepath):
                os.remove(final_filepath)
            os.rename(temp_filepath, final_filepath)

        album_name = track.album.title if (hasattr(track, 'album') and track.album) else "Singles"
        self._write_metadata(final_filepath, track.title, track.artist, album_name)
        print(f"[YuEProvider] Àudio generat i desat amb èxit a {final_filepath}")
        return final_filepath

    def _write_metadata(self, filepath, title, artist, album):
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
            print(f"[YuEProvider] Error escrivint metadades: {e}")
