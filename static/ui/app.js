
// YouTube Preview Updater
function updateYTPreview() {
  const on = ui.albumOn;
  const manual = on && ui.albumMode === 'manual';
  
  let totalTitle = $('title') ? $('title').value.trim() : '';
  if (!totalTitle) totalTitle = 'Sense Títol';
  const artist = $('artist') ? $('artist').value.trim() : '';
  
  let totalSeconds = 0;
  let trackDurations = [];
  
  const blockNodes = document.querySelectorAll('.track-block');
  if (on) {
    if (manual) {
      blockNodes.forEach(b => {
        const d = parseInt(b.querySelector('.track-duration').value, 10) || 30;
        trackDurations.push(d);
        totalSeconds += d;
      });
    } else {
      const count = parseInt($('autoCount').value, 10) || 1;
      const dur = parseInt($('autoDuration').value, 10) || 30;
      for (let i=0; i<count; i++) { trackDurations.push(dur); totalSeconds += dur; }
    }
  } else {
    if (blockNodes[0]) {
      const d = parseInt(blockNodes[0].querySelector('.track-duration').value, 10) || 30;
      trackDurations.push(d);
      totalSeconds += d;
    }
  }
  
  if (totalSeconds === 0) totalSeconds = 30;
  
  const ytTitle = document.getElementById('ytTitlePreview');
  if(ytTitle) ytTitle.textContent = `${totalTitle} - ${artist || 'Artista'}`;
  
  const ytTime = document.getElementById('ytTimePreview');
    if (ytTime) {
      const zeroTime = totalSeconds >= 3600 ? '0:00:00' : '0:00';
      ytTime.textContent = `${zeroTime} / ${fmtTime(totalSeconds)}`;
    }
  
  const chapters = document.getElementById('ytChapters');
  if(chapters) {
    chapters.innerHTML = trackDurations.map(d => `<div class="yt-chapter-mark" style="flex: ${d}"></div>`).join('');
  }
}

/* Arcàdia Lliure Studio — lògica de la interfície.
   Totes les crides al servidor passen per api(); els colors dels gràfics es llegeixen
   dels tokens CSS perquè la identitat visual visqui en un únic lloc. */
"use strict";

// ===================== Iconografia (SVG, traç consistent) =====================
const ICONS = {
  play: '<path d="M7 5v14l12-7z"/>',
  pause: '<path d="M8 5v14M16 5v14"/>',
  prev: '<path d="M6 6v12M18 6l-8 6 8 6z"/>',
  next: '<path d="M18 6v12M6 6l8 6-8 6z"/>',
  library: '<path d="M4 7h16M4 12h16M4 17h10"/>',
  album: '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="2.2"/>',
  track: '<path d="M9 18V6l10-2v12"/><circle cx="6" cy="18" r="3"/><circle cx="16" cy="16" r="3"/>',
  spark: '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/>',
  star: '<path d="M12 4l2.4 5 5.4.7-4 3.7 1 5.4L12 16.3l-4.8 2.5 1-5.4-4-3.7 5.4-.7z"/>',
  clock: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
  youtube: '<rect x="3" y="6" width="18" height="12" rx="3.5"/><path d="M10.5 9.5v5l4-2.5z"/>',
  file: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/>',
  edit: '<path d="M4 20h4L19 9l-4-4L4 16z"/>',
  rename: '<path d="M5 6h14M12 6v13M9 19h6"/>',
  modify: '<path d="M4 7h9M17 7h3M4 17h3M11 17h9"/><circle cx="15" cy="7" r="2"/><circle cx="9" cy="17" r="2"/>',
  regen: '<path d="M19.5 12a7.5 7.5 0 1 1-2.2-5.3"/><path d="M19.5 4.5V9h-4.5"/>',
  extend: '<path d="M4 12h12M12 6l6 6-6 6"/>',
  undo: '<path d="M9 14L4 9l5-5"/><path d="M4 9h10a6 6 0 0 1 0 12h-3"/>',
  redo: '<path d="M15 14l5-5-5-5"/><path d="M20 9H10a6 6 0 0 0 0 12h3"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  close: '<path d="M6 6l12 12M18 6L6 18"/>',
  download: '<path d="M12 4v11"/><path d="M7 11l5 5 5-5"/><path d="M5 20h14"/>',
  trash: '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/>',
  chevron: '<path d="M6 9l6 6 6-6"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  upload: '<path d="M12 16V5"/><path d="M7 10l5-5 5 5"/><path d="M5 20h14"/>',
  image: '<rect x="3" y="4" width="18" height="16" rx="2.5"/><circle cx="9" cy="10" r="2"/><path d="M21 17l-5-5-9 9"/>',
  alert: '<path d="M12 4l9 16H3z"/><path d="M12 10v4M12 17.5v.5"/>',
};

function icon(name) {
  return `<svg class="ic" viewBox="0 0 24 24" aria-hidden="true">${ICONS[name] || ''}</svg>`;
}

function hydrateIcons(root = document) {
  root.querySelectorAll('[data-icon]').forEach(el => { el.innerHTML = icon(el.dataset.icon); });
}

// ===================== Utilitats =====================
const $ = (id) => document.getElementById(id);
const MAX_GEN_SECONDS = 30;
const INSTRUMENTS = [
  { id: "Piano", icon: "mdi:piano", color: "black", style: "" },
  { id: "Clavicord", icon: "mdi:piano", color: "%238B4513", style: "transform: scaleX(-1);" },
  { id: "Synth", icon: "game-icons:piano-keys", color: "%239400D3", style: "" },
  { id: "Acoustic Guitar", icon: "mdi:guitar-acoustic", color: "%23D2691E", style: "" },
  { id: "Spanish Guitar", icon: "mdi:guitar-acoustic", color: "%238B0000", style: "transform: rotate(15deg);" },
  { id: "Elec Guitar", icon: "mdi:guitar-electric", color: "%231E90FF", style: "" },
  { id: "Bass", icon: "mdi:guitar-electric", color: "%2332CD32", style: "transform: scale(1.1) rotate(-10deg);" },
  { id: "Ukulele", icon: "qlementine-icons:ukulele-24", color: "%23DEB887", style: "" },
  { id: "Harp", icon: "game-icons:harp", color: "%23DAA520", style: "" },
  { id: "Contrabass", icon: "qlementine-icons:cello-24", color: "%235C4033", style: "transform: scale(1.3);" },
  { id: "Cello", icon: "qlementine-icons:cello-24", color: "%238B4513", style: "" },
  { id: "Violin", icon: "mdi:violin", color: "%23A0522D", style: "" },
  { id: "Flute", icon: "game-icons:flute", color: "%23708090", style: "" },
  { id: "Clarinet", icon: "game-icons:clarinet", color: "black", style: "" },
  { id: "Oboe", icon: "game-icons:clarinet", color: "%232F4F4F", style: "transform: scaleY(-1);" },
  { id: "Fagot", icon: "game-icons:bassoon", color: "%238B4513", style: "" },
  { id: "Gralla", icon: "game-icons:clarinet", color: "%23CD853F", style: "" },
  { id: "Saxophone", icon: "mdi:saxophone", color: "%23DAA520", style: "" },
  { id: "Trumpet", icon: "mdi:trumpet", color: "%23FFA500", style: "" },
  { id: "Trombone", icon: "game-icons:trombone", color: "%23DAA520", style: "" },
  { id: "Harmonica", icon: "qlementine-icons:harmonica-16", color: "%234682B4", style: "transform: scale(1.3);" },
  { id: "Drums", icon: "lucide:drum", color: "%23FF4500", style: "" },
  { id: "Choir", icon: "lucide:mic", color: "black", style: "" },
];

const ui = {
  albumOn: false,
  albumMode: 'auto',
  inspTab: 'fav',
  activeInsp: null,
  insp: { favorites: [], recents: [], cleanup_days: 30, max_seconds: 30 },
  library: null,
  collapsed: new Set(),
  editor: null,
  lastQueueIds: [],
};
const globalStates = {};
INSTRUMENTS.forEach(i => { globalStates[i.id] = 0; });

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function fmtTime(seconds) {
  if (!isFinite(seconds) || seconds < 0) return '0:00';
  const s = Math.floor(seconds);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = String(s % 60).padStart(2, '0');
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${sec}`;
  return `${m}:${sec}`;
}
function clamp(v, lo, hi) { return Math.min(hi, Math.max(lo, v)); }

function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

async function api(url, options = {}) {
  const opts = { headers: {}, ...options };
  if (opts.body && !(opts.body instanceof FormData)) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(opts.body);
  }
  const res = await fetch(url, opts);
  const isJson = (res.headers.get('content-type') || '').includes('application/json');
  const data = isJson ? await res.json() : null;
  if (!res.ok) throw new Error((data && data.error) || `Error ${res.status}`);
  return data;
}

function toast(message, type = 'info') {
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.textContent = message;
  $('toasts').appendChild(el);
  setTimeout(() => el.classList.add('out'), 3800);
  setTimeout(() => el.remove(), 4300);
}

function showOverlay(html, cls = '') {
  const card = $('overlayCard');
  card.className = `dialog ${cls}`.trim();
  card.innerHTML = html;
  $('overlay').classList.add('open');
  return card;
}

function closeOverlay() {
  $('overlay').classList.remove('open');
  $('overlayCard').innerHTML = '';
}

function askConfirm(message, okLabel = 'Confirmar', danger = false) {
  return new Promise(resolve => {
    showOverlay(`
        <h3>${esc(message)}</h3>
        <div class="dialog-actions">
            <button class="btn btn-ghost" id="dlgNo">Cancel·lar</button>
            <button class="btn ${danger ? 'btn-danger' : 'btn-primary'}" id="dlgYes">${esc(okLabel)}</button>
        </div>`, 'dialog-sm');
    $('dlgNo').onclick = () => { closeOverlay(); resolve(false); };
    $('dlgYes').onclick = () => { closeOverlay(); resolve(true); };
  });
}

function askText(title, value = '') {
  return new Promise(resolve => {
    showOverlay(`
        <h3>${esc(title)}</h3>
        <input type="text" id="dlgText" class="field" value="${esc(value)}" maxlength="255">
        <div class="dialog-actions">
            <button class="btn btn-ghost" id="dlgNo">Cancel·lar</button>
            <button class="btn btn-primary" id="dlgYes">Desar</button>
        </div>`, 'dialog-sm');
    const input = $('dlgText');
    input.focus();
    input.select();
    const done = (result) => { closeOverlay(); resolve(result); };
    $('dlgNo').onclick = () => done(null);
    $('dlgYes').onclick = () => done(input.value.trim() || null);
    input.addEventListener('keydown', e => { if (e.key === 'Enter') done(input.value.trim() || null); });
  });
}

function downloadUrl(url) {
  const a = document.createElement('a');
  a.href = url;
  a.download = '';
  document.body.appendChild(a);
  a.click();
  a.remove();
}

// ===================== Instruments (wizard) =====================
function prefixFromStates(states) {
  const req = [], opt = [], forbid = [];
  Object.keys(states).forEach(k => {
    if (states[k] === 1) req.push(k);
    if (states[k] === 2) opt.push(k);
    if (states[k] === 3) forbid.push(k);
  });
  let prefix = '';
  if (req.length) prefix += `Instrumentation: ${req.join(', ')}. `;
  if (opt.length) prefix += `Optional instruments: ${opt.join(', ')}. `;
  if (forbid.length) prefix += `NO ${forbid.join(', NO ')}. `;
  return prefix.trim();
}

function instrumentButton(inst, state, mini) {
  const size = mini ? 'mini' : '';
  return `<button type="button" class="inst-btn inst-state-${state} ${size}" data-inst="${esc(inst.id)}" title="${esc(inst.id)}">
      <img src="https://api.iconify.design/${inst.icon}.svg?color=${inst.color}" alt="" style="${inst.style}">
      <span class="inst-name">${esc(inst.id)}</span></button>`;
}

function renderWizard(container, states, onChange, mini = false) {
  container.innerHTML = INSTRUMENTS.map(inst => instrumentButton(inst, states[inst.id] || 0, mini)).join('');
  container.querySelectorAll('.inst-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.dataset.inst;
      states[id] = ((states[id] || 0) + 1) % 4;
      btn.className = `inst-btn inst-state-${states[id]} ${mini ? 'mini' : ''}`;
      if (onChange) onChange();
    });
  });
}

// ===================== Caràtula i ComfyUI =====================
let comfyModelsCache = [];

async function loadComfyModels() {
  try {
    const data = await api('/api/comfyui/models');
    comfyModelsCache = data.models;
    const sel = $('comfyModelSelect');
    sel.innerHTML = data.models.map(m => `<option value="${esc(m.filename)}">${esc(m.name)} ${m.downloaded ? '✅' : '❌'}</option>`).join('');
    updateDeleteBtn();
    const busy = data.download_status.status === 'downloading';
    $('downloadProgressBox').hidden = !busy;
    $('downloadProgressBar').style.width = `${data.download_status.progress || 0}%`;
    $('btnComfyUI').disabled = busy;
    $('btnDeleteModel').disabled = busy;
    if (busy) setTimeout(loadComfyModels, 1000);
  } catch (e) {
    $('comfyModelSelect').innerHTML = '<option>Error connectant...</option>';
  }
}

function updateDeleteBtn() {
  const modelObj = comfyModelsCache.find(m => m.filename === $('comfyModelSelect').value);
  $('btnDeleteModel').hidden = !(modelObj && modelObj.downloaded);
}

async function deleteComfyModel() {
  const modelObj = comfyModelsCache.find(m => m.filename === $('comfyModelSelect').value);
  if (!modelObj || !modelObj.downloaded) return;
  const ok = await askConfirm(`Vols esborrar el model ${modelObj.name}? Pots tornar a descarregar-lo més tard.`, 'Esborrar', true);
  if (!ok) return;
  await api('/api/comfyui/delete', { method: 'POST', body: { filename: modelObj.filename } });
  loadComfyModels();
}

async function uploadCover(input) {
  if (!input.files || !input.files.length) return;
  const file = input.files[0];
  const formData = new FormData();
  formData.append('file', file);
  try {
    const data = await api('/api/upload_cover', { method: 'POST', body: formData });
    setCoverPreview(data.url, file.type.startsWith('video/'));
    $('currentCoverPath').value = data.cover_path;
  } catch (e) {
    toast(`Error pujant la caràtula: ${e.message}`, 'error');
  }
}

async function generateCoverComfyUI() {
  const modelObj = comfyModelsCache.find(m => m.filename === $('comfyModelSelect').value);
  if (modelObj && !modelObj.downloaded) {
    const ok = await askConfirm(`El model ${modelObj.name} no està descarregat. Vols descarregar-lo ara? Ocupa diversos GB.`, 'Descarregar');
    if (ok) {
      await api('/api/comfyui/download', { method: 'POST', body: { filename: modelObj.filename } });
      loadComfyModels();
    }
    return;
  }
  let prompt = $('coverPrompt').value.trim() || $('albumPrompt').value.trim();
  if (!prompt) {
    const firstBlock = blocks()[0];
    prompt = firstBlock ? firstBlock.querySelector('.prompt-input').value.trim() : '';
  }
  const btn = $('btnComfyUI');
  const original = btn.innerHTML;
  btn.innerHTML = '<span class="spinner"></span> Generant...';
  btn.disabled = true;
  try {
    const data = await api('/api/comfyui', {
      method: 'POST',
      body: { prompt: prompt || 'abstract music concept', model: $('comfyModelSelect').value }
    });
    setCoverPreview(data.url, false);
    $('currentCoverPath').value = data.cover_path;
  } catch (e) {
    toast(`ComfyUI: ${e.message}`, 'error');
  } finally {
    btn.innerHTML = original;
    btn.disabled = false;
  }
}

function setCoverPreview(url, isVideo) {
  const img = $('coverImgPreview');
  const vid = $('coverVidPreview');
  $('coverBox').classList.add('has-media');
  img.hidden = isVideo;
  vid.hidden = !isVideo;
  if (isVideo) vid.src = url; else img.src = url;
}

// ===================== Mode àlbum i pistes del formulari =====================
function blocks() {
  return [...$('tracksContainer').querySelectorAll('.track-block')];
}

function createBlock(index) {
  const el = document.createElement('article');
  el.className = 'track-block';
  el.wizardStates = {};
  INSTRUMENTS.forEach(i => { el.wizardStates[i.id] = 0; });
  el.innerHTML = `
      <div class="track-block-head">
          <span class="kicker track-label"></span>
          ${ui.albumOn && ui.albumMode === 'manual' ? `<button type="button" class="icon-btn danger" data-remove title="Eliminar pista">${icon('close')}</button>` : ''}
      </div>
      ${ui.albumOn ? `<input type="text" class="field track-title" placeholder="Títol de la pista">` : ''}
      <textarea class="field prompt-input" rows="2" placeholder="Estil, emoció o instruments d'aquesta pista..."></textarea>
      <div class="inline-row">
          <span class="label-inline">Durada (s)</span>
          <input type="number" class="field field-sm track-duration" value="30" min="1" style="width:110px">
      </div>
      <div class="mini-wizard"></div>`;
  const removeBtn = el.querySelector('[data-remove]');
  
  const titleInput = el.querySelector('.track-title');
  if (titleInput) titleInput.addEventListener('input', updateYTPreview);
  if (removeBtn) removeBtn.addEventListener('click', () => { el.remove(); refreshBlocks();
  updateYTPreview(); });
  $('tracksContainer').appendChild(el);
  return el;
}

function refreshBlocks() {
  const list = blocks();
  const sameGlobal = $('sameInstruments').checked;
  list.forEach((block, i) => {
    block.querySelector('.track-label').textContent = ui.albumOn ? `Pista ${i + 1}` : 'Pista';
    const mini = block.querySelector('.mini-wizard');
    const showMini = ui.albumOn && ui.albumMode === 'manual' && !sameGlobal;
    mini.hidden = !showMini;
    if (showMini) renderWizard(mini, block.wizardStates, null, true);
    block.querySelector('.track-title') && (block.querySelector('.track-title').placeholder = `Títol de la pista ${i + 1}`);
  });
  $('manualCount').value = list.length;
}

function setBlockCount(count) {
  const container = $('tracksContainer');
  const previous = blocks().map(b => ({
    title: b.querySelector('.track-title') ? b.querySelector('.track-title').value : '',
    prompt: b.querySelector('.prompt-input').value,
    duration: b.querySelector('.track-duration').value,
    states: b.wizardStates,
  }));
  container.innerHTML = '';
  for (let i = 0; i < count; i++) {
    const block = createBlock(i);
    const old = previous[i];
    if (old) {
      if (block.querySelector('.track-title')) block.querySelector('.track-title').value = old.title;
      block.querySelector('.prompt-input').value = old.prompt;
      block.querySelector('.track-duration').value = old.duration;
      block.wizardStates = old.states;
    }
  }
  refreshBlocks();
  updateYTPreview();
}

function applyAlbumMode() {
  const on = ui.albumOn;
  const manual = on && ui.albumMode === 'manual';
  
  if (!on) {
    ui.targetAlbumId = null;
      updateYTPreview();
    ui.targetAlbumTitle = null;
  }
  
  $('titleLabel').textContent = on ? 'Títol àlbum' : 'Títol cançó';
  $('title').placeholder = on ? "Nom de l'àlbum (obligatori)..." : 'Escriu el títol...';
  $('studioTitle').innerHTML = ui.targetAlbumId ? `Afegint a l'àlbum <strong class="text-primary">${esc(ui.targetAlbumTitle)}</strong>` : (on ? 'Àlbum' : 'Pista única');
  $('albumPanel').hidden = !on;
  $('autoFields').hidden = !on || manual;
  $('manualFields').hidden = !manual;
  $('sameWrap').hidden = !manual;
  $('albumModeHint').textContent = on
    ? (ui.albumMode === 'auto'
      ? 'Un prompt global i la mateixa durada per a totes les pistes. Els noms provisionals són NomAlbum_1, _2...'
      : 'Configura cada pista. Cada una s\'encadena amb l\'anterior (model Melody).')
    : '';
  $('tracksTitle').textContent = manual ? 'Pistes' : 'Pista';
  $('tracksContainer').hidden = on && ui.albumMode === 'auto';
  $('instrumentGrid').closest('.instruments').hidden = manual && !$('sameInstruments').checked;
  document.querySelectorAll('#albumModeSeg button').forEach(b => b.classList.toggle('active', b.dataset.mode === ui.albumMode));
  if (manual) setBlockCount(parseInt($('manualCount').value, 10) || 1);
  else setBlockCount(1);
  if (!on) $('tracksContainer').hidden = false;
}

// ===================== Enviament de feines =====================
async function submitJob() {
  const btn = $('submitBtn');
  const title = $('title').value.trim();
  const artist = $('artist').value.trim() || 'Unknown Artist';
  const model = $('model').value;
  const coverPath = $('currentCoverPath').value || null;
  const inspirationId = ui.activeInsp ? ui.activeInsp.id : null;
  const globalPrefix = prefixFromStates(globalStates);
  if (!title) return toast(ui.albumOn ? "El nom de l'àlbum és obligatori" : 'Falta el títol de la cançó', 'warning');

  btn.disabled = true;
  try {
    if (!ui.albumOn) {
      const block = blocks()[0];
      const prompt = [globalPrefix, block.querySelector('.prompt-input').value.trim()].filter(Boolean).join(' ');
      await api('/api/generate/single', {
        method: 'POST',
        body: {
          title, artist, model, prompt, cover_path: coverPath, inspiration_id: inspirationId,
          duration: parseInt(block.querySelector('.track-duration').value, 10) || 30,
        }
      });
    } else if (ui.albumMode === 'auto') {
      await api('/api/generate/album/auto', {
        method: 'POST',
        body: {
          album_id: ui.targetAlbumId, album_title: title, artist, model, cover_path: coverPath, inspiration_id: inspirationId,
          global_prompt: $('albumPrompt').value.trim(),
          instrument_prefix: globalPrefix,
          track_count: parseInt($('autoCount').value, 10),
          duration: parseInt($('autoDuration').value, 10),
        }
      });
    } else {
      const albumPrompt = $('albumPrompt').value.trim();
      const sameGlobal = $('sameInstruments').checked;
      const tracks = blocks().map((block, i) => ({
        title: (block.querySelector('.track-title').value || '').trim() || `Pista ${i + 1}`,
        prompt: [albumPrompt, sameGlobal ? globalPrefix : prefixFromStates(block.wizardStates), block.querySelector('.prompt-input').value.trim()].filter(Boolean).join(' '),
        duration: parseInt(block.querySelector('.track-duration').value, 10) || 30,
      }));
      await api('/api/generate/album', {
        method: 'POST',
        body: { album_id: ui.targetAlbumId, album_title: title, artist, model, tracks, cover_path: coverPath, inspiration_id: inspirationId }
      });
    }
    toast('Afegit a la cua de treball', 'success');
    pollQueue();
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
  }
}

async function pollQueue() {
  $('queueSpinner').hidden = false;
  try {
    const data = await api('/api/status');
    const list = $('queueList');
    if (!data.queue.length) {
      list.innerHTML = `<li class="empty">${icon('check')}<br>Cua buida. Tot llest.</li>`;
    } else {
      list.innerHTML = data.queue.map(t => {
        const thumb = t.cover_path ? `<img class="queue-thumb" src="${esc(t.cover_path)}" alt="">` : `<span class="queue-thumb">${icon('track')}</span>`;
        const badge = t.status === 'generating'
          ? '<span class="badge badge-warning"><span class="spinner"></span>Generant</span>'
          : '<span class="badge">Pendent</span>';
        return `<li class="queue-item">${thumb}<div class="info"><strong>${esc(t.title)}</strong><small>${esc((t.prompt || '').slice(0, 48))}</small></div>${badge}</li>`;
      }).join('');
    }
    const currentIds = data.queue.map(q => q.id);
    if (ui.lastQueueIds.length > 0 && currentIds.length < ui.lastQueueIds.length) playDing();
    ui.lastQueueIds = currentIds;
    if (currentIds.length) setTimeout(pollQueue, 3000);
  } finally {
    $('queueSpinner').hidden = true;
  }
}

let audioCtx = null;
function playDing() {
  if (!$('notifySound').checked) return;
  try {
    audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(880, audioCtx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(440, audioCtx.currentTime + 0.5);
    gain.gain.setValueAtTime(0.4, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.5);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.5);
  } catch (e) { /* sense àudio disponible */ }
}

// ===================== Tasques en segon pla =====================
function trackJob(jobId, label, onDone) {
  const tray = $('taskTray');
  tray.hidden = false;
  const item = document.createElement('div');
  item.className = 'task';
  item.innerHTML = `<div class="task-head"><span class="spinner"></span><strong>${esc(label)}</strong></div>
      <div class="progress"><span></span></div><small class="task-msg muted">Iniciant...</small>`;
  tray.appendChild(item);

  const finish = (delay) => setTimeout(() => {
    item.remove();
    if (!tray.children.length) tray.hidden = true;
  }, delay);

  const poll = async () => {
    try {
      const job = await api(`/api/jobs/${jobId}`);
      item.querySelector('.progress > span').style.width = `${job.progress || 0}%`;
      item.querySelector('.task-msg').textContent = job.message || '';
      if (job.status === 'done') {
        if (onDone) onDone(job);
        finish(1500);
        return;
      }
      if (job.status === 'error') {
        item.classList.add('task-error');
        item.querySelector('.task-msg').textContent = job.error || 'Error desconegut';
        toast(job.error || 'La tasca ha fallat', 'error');
        finish(6000);
        return;
      }
      setTimeout(poll, 1000);
    } catch (e) {
      item.classList.add('task-error');
      item.querySelector('.task-msg').textContent = e.message;
      finish(6000);
    }
  };
  poll();
}

// ===================== Inspiracions =====================
async function loadInspirations() {
  try {
    ui.insp = await api('/api/inspirations');
    renderInspirations();
    renderActiveInspiration();
  } catch (e) {
    toast(`No s'han pogut carregar les inspiracions: ${e.message}`, 'error');
  }
}

function renderActiveInspiration() {
  const holder = $('activeInspiration');
  if (!ui.activeInsp) { holder.innerHTML = ''; return; }
  holder.innerHTML = `<div class="chip"><span>Inspiració activa · ${esc(ui.activeInsp.name)}</span>
      <button type="button" data-act="clear-insp" title="Desactivar inspiració">${icon('close')}</button></div>`;
}

function renderInspirations() {
  document.querySelectorAll('#inspTabs button').forEach(b => b.classList.toggle('active', b.dataset.tab === ui.inspTab));
  const holder = $('inspContent');
  if (ui.inspTab === 'new') {
    holder.innerHTML = `
        <div class="import-grid">
            <div class="inline-row wrap">
                <button class="btn btn-ghost" data-act="pick-file">${icon('upload')} Fitxer local</button>
                <span class="muted small">Àudio o vídeo. Si dura més de ${ui.insp.max_seconds} s podràs triar el fragment.</span>
                <input type="file" id="inspFile" hidden accept="audio/*,video/*">
            </div>
            <form class="inline-row wrap" id="ytForm">
                <input type="url" id="ytUrl" class="field" placeholder="Enllaç de YouTube..." style="flex:1;min-width:220px">
                <button type="submit" class="btn btn-primary">${icon('youtube')} Importar</button>
            </form>
        </div>`;
    return;
  }
  const list = ui.inspTab === 'fav' ? ui.insp.favorites : ui.insp.recents;
  const cleanupOptions = [[10, '10 dies'], [30, '30 dies'], [90, '90 dies'], [0, 'Mai']];
  const rows = list.length
    ? list.map(i => {
      const active = ui.activeInsp && ui.activeInsp.id === i.id;
      return `<li class="insp-row ${active ? 'is-active' : ''}">
          <button type="button" class="insp-main" data-act="use-insp" data-id="${i.id}">
              ${icon(i.source === 'youtube' ? 'youtube' : 'file')}
              <span><strong>${esc(i.name)}</strong><small>${fmtTime(i.duration)} · ${i.source === 'youtube' ? 'YouTube' : 'Fitxer local'}</small></span>
          </button>
          <button type="button" class="icon-btn ${i.favorite ? 'on' : ''}" data-act="fav-insp" data-id="${i.id}" data-fav="${!i.favorite}" title="${i.favorite ? 'Treure de favorits' : 'Afegir a favorits'}">${icon('star')}</button>
          <button type="button" class="icon-btn danger" data-act="del-insp" data-id="${i.id}" title="Esborrar">${icon('trash')}</button>
      </li>`;
    }).join('')
    : `<div class="empty">${ui.inspTab === 'fav' ? 'Encara no tens favorits. Marca una inspiració amb l\'estrella.' : 'No hi ha inspiracions recents.'}</div>`;
  holder.innerHTML = `<ul class="list">${rows}</ul>
      ${ui.inspTab === 'rec' ? `<div class="cleanup-row">
          <span>Neteja automàtica de les recents no favorites</span>
          <select id="cleanupSelect" class="field field-sm" style="width:auto">
              ${cleanupOptions.map(([v, l]) => `<option value="${v}" ${v === ui.insp.cleanup_days ? 'selected' : ''}>${l}</option>`).join('')}
          </select></div>` : ''}`;
}

async function activateInspiration(id) {
  try {
    const data = await api(`/api/inspirations/${id}/use`, { method: 'POST' });
    ui.activeInsp = data.inspiration;
    renderActiveInspiration();
    await loadInspirations();
    toast(`Inspiració activada: ${data.inspiration.name}`, 'success');
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function importYoutube(url) {
  const data = await api('/api/inspirations/youtube', { method: 'POST', body: { url } });
  trackJob(data.job_id, 'Importació de YouTube', onImportDone);
}

async function importLocal(file) {
  const formData = new FormData();
  formData.append('file', file);
  const data = await api('/api/inspirations/upload', { method: 'POST', body: formData });
  trackJob(data.job_id, file.name, onImportDone);
}

function onImportDone(job) {
  const result = job.result || {};
  if (result.requires_selection) {
    openSelector(result.import_id);
  } else {
    toast('Inspiració desada a la biblioteca', 'success');
    loadInspirations();
  }
}

function drawWave(canvas, peaks, opts) {
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;
  canvas.width = Math.round(w * dpr);
  canvas.height = Math.round(h * dpr);
  const ctx = canvas.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);

  const accent = cssVar('--c-accent');
  const soft = cssVar('--c-accent-soft');
  const strong = cssVar('--c-accent-strong');
  const muted = cssVar('--c-border-strong');
  const amber = cssVar('--c-amber');
  const duration = opts.duration || 1;
  const toX = (t) => (t / duration) * w;

  (opts.regions || []).forEach(r => {
    const x0 = toX(r.startTime);
    const x1 = toX(r.endTime);
    ctx.fillStyle = r.id === opts.selectedId ? strong : soft;
    ctx.fillRect(x0, 0, x1 - x0, h);
    ctx.strokeStyle = r.id === opts.selectedId ? accent : 'transparent';
    ctx.lineWidth = 1.5;
    ctx.strokeRect(x0 + 0.75, 0.75, x1 - x0 - 1.5, h - 1.5);
  });
  (opts.selection ? [opts.selection] : []).forEach(sel => {
    const x0 = toX(sel.start);
    const x1 = toX(sel.end);
    ctx.fillStyle = soft;
    ctx.fillRect(x0, 0, x1 - x0, h);
  });

  const bw = w / Math.max(1, peaks.length);
  const mid = h / 2;
  peaks.forEach((p, i) => {
    const t = (i / peaks.length) * duration;
    const inside = opts.selection
      ? t >= opts.selection.start && t <= opts.selection.end
      : (opts.regions || []).some(r => t >= r.startTime && t <= r.endTime);
    const bh = Math.max(2, p * h * 0.8);
    ctx.fillStyle = inside ? accent : muted;
    ctx.fillRect(i * bw + bw * 0.2, mid - bh / 2, Math.max(1, bw * 0.6), bh);
  });

  if (opts.handles && opts.selection) {
    [opts.selection.start, opts.selection.end].forEach(t => {
      ctx.fillStyle = accent;
      ctx.fillRect(toX(t) - 1.5, 0, 3, h);
    });
  }
  if (opts.playhead !== undefined && opts.playhead !== null) {
    ctx.fillStyle = amber;
    ctx.fillRect(toX(opts.playhead) - 1, 0, 2, h);
  }
}

// ----- Selector temporal (inspiració > durada màxima) -----
async function openSelector(importId) {
  let data;
  try {
    data = await api(`/api/inspirations/imports/${importId}`);
  } catch (e) {
    toast(e.message, 'error');
    return;
  }
  const max = data.max_seconds;
  const sel = { start: 0, end: Math.min(data.duration, max) };
  let drag = null;

  showOverlay(`
      <div class="dialog-head">
          <div><span class="kicker">Selector de fragment</span><h3>${esc(data.name)}</h3></div>
          <span class="badge badge-accent">Màxim ${max} s</span>
      </div>
      <p class="note">Arrossega els extrems de la selecció. El fragment es repeteix en bucle mentre l'escoltes.</p>
      <div class="wave-wrap"><canvas id="selCanvas" class="wave" style="height:140px"></canvas></div>
      <div class="selector-meta">
          <span>Inici <strong id="selStart">0:00</strong> · Fi <strong id="selEnd">0:00</strong></span>
          <span>Durada <strong id="selLen">0,0 s</strong> de ${fmtTime(data.duration)} totals</span>
      </div>
      <audio id="selAudio" preload="auto" src="${data.audio_url}"></audio>
      <div class="dialog-actions">
          <button class="btn btn-ghost" id="selPlay">${icon('play')} Reproduir fragment</button>
          <button class="btn btn-ghost" id="selDiscard">Descartar</button>
          <button class="btn btn-primary" id="selAccept">${icon('check')} Crear inspiració</button>
      </div>`, 'dialog-lg');

  const canvas = $('selCanvas');
  const audio = $('selAudio');

  const render = () => {
    drawWave(canvas, data.peaks, {
      duration: data.duration,
      selection: { start: sel.start, end: sel.end },
      handles: true,
      playhead: audio.currentTime,
    });
    $('selStart').textContent = fmtTime(sel.start);
    $('selEnd').textContent = fmtTime(sel.end);
    $('selLen').textContent = `${(sel.end - sel.start).toFixed(1).replace('.', ',')} s`;
  };

  const timeAt = (e) => {
    const rect = canvas.getBoundingClientRect();
    return ((e.clientX - rect.left) / rect.width) * data.duration;
  };

  const moveHandle = (t) => {
    t = clamp(t, 0, data.duration);
    if (drag === 'start') {
      sel.start = Math.min(t, sel.end - 1);
      if (sel.end - sel.start > max) sel.end = sel.start + max;
    } else {
      sel.end = Math.max(t, sel.start + 1);
      if (sel.end - sel.start > max) sel.start = sel.end - max;
    }
    sel.start = clamp(sel.start, 0, data.duration);
    sel.end = clamp(sel.end, 0, data.duration);
    render();
  };

  canvas.addEventListener('pointerdown', (e) => {
    const t = timeAt(e);
    drag = Math.abs(t - sel.start) < Math.abs(t - sel.end) ? 'start' : 'end';
    canvas.setPointerCapture(e.pointerId);
    moveHandle(t);
  });
  canvas.addEventListener('pointermove', (e) => { if (drag) moveHandle(timeAt(e)); });
  canvas.addEventListener('pointerup', () => { drag = null; });
  audio.addEventListener('timeupdate', () => {
    if (audio.currentTime >= sel.end) audio.currentTime = sel.start;
    render();
  });

  $('selPlay').onclick = () => {
    if (audio.paused) {
      if (audio.currentTime < sel.start || audio.currentTime >= sel.end) audio.currentTime = sel.start;
      audio.play();
    } else {
      audio.pause();
    }
  };

  $('selDiscard').onclick = async () => {
    audio.pause();
    closeOverlay();
    try { await api(`/api/inspirations/imports/${importId}`, { method: 'DELETE' }); } catch (e) { /* ja descartada */ }
  };

  $('selAccept').onclick = async () => {
    try {
      audio.pause();
      const res = await api(`/api/inspirations/imports/${importId}/accept`, {
        method: 'POST', body: { start: sel.start, end: sel.end }
      });
      closeOverlay();
      ui.activeInsp = res.inspiration;
      toast(`Inspiració creada i activada: ${res.inspiration.name}`, 'success');
      loadInspirations();
    } catch (e) {
      toast(e.message, 'error');
    }
  };

  window.addEventListener('resize', render, { once: false });
  render();
}

// ===================== Biblioteca =====================
function findAlbum(id) {
  return (ui.library && ui.library.albums.find(a => a.id === id)) || null;
}

function findTrack(id) {
  if (!ui.library) return null;
  for (const album of ui.library.albums) {
    const t = album.tracks.find(x => x.id === id);
    if (t) return t;
  }
  return ui.library.singles.find(t => t.id === id) || null;
}

async function loadLibrary() {
  try {
    ui.library = await api('/api/library');
    renderLibrary();
  } catch (e) {
    $('libraryContainer').innerHTML = `<div class="library-empty">${icon('alert')}<span>${esc(e.message)}</span></div>`;
  }
}

function trackRow(t, album, order) {
  const cover = t.cover_path || (album && album.cover_path);
  const done = t.status === 'done' && t.filepath;
  const statusBadge = done ? ''
    : t.status === 'error' ? '<span class="badge badge-error">Error</span>'
      : `<span class="badge badge-warning"><span class="spinner"></span>${esc(t.status)}</span>`;
  const errorBox = t.status === 'error' && t.error_msg ? `<pre class="error-box">${esc(t.error_msg)}</pre>` : '';
  const playBtn = done ? `<button class="icon-btn" data-act="play-track" data-id="${t.id}" title="Reproduir">${icon('play')}</button>` : '';
  const editBtn = done ? `<button class="btn btn-ghost btn-sm" data-act="edit-track" data-id="${t.id}">${icon('modify')} Editar</button>` : '';
  const exportLinks = done
    ? `<a class="btn btn-ghost btn-sm" href="/api/export/mp3/${t.id}" download>${icon('download')} MP3</a>${cover ? `<a class="btn btn-ghost btn-sm" href="/api/export/mp4/${t.id}" download>${icon('image')} MP4</a>` : ''}`
    : '';
  return `<li class="track-row">
      <span class="track-order mono">${order !== null ? String(order).padStart(2, '0') : '·'}</span>
      <div class="track-main">
          <strong>${esc(t.title)}</strong>
          <span class="muted small">${esc(t.artist || '')} ${statusBadge}</span>
          ${errorBox}
      </div>
      <div class="track-actions">
          ${playBtn}${editBtn}${exportLinks}
          <button class="icon-btn" data-act="rename-track" data-id="${t.id}" title="Canviar el nom">${icon('rename')}</button>
          <button class="icon-btn danger" data-act="delete-track" data-id="${t.id}" title="Esborrar">${icon('trash')}</button>
      </div>
  </li>`;
}

function albumCard(album) {
  const collapsed = ui.collapsed.has(album.id);
  const doneCount = album.tracks.filter(t => t.status === 'done' && t.filepath).length;
  const cover = album.cover_path
    ? `<img class="album-cover-img" src="${esc(album.cover_path)}" alt="">`
    : `<span class="album-cover-ph">${icon('album')}</span>`;
  return `<section class="album" data-album-id="${album.id}">
      <header class="album-head">
          <button class="icon-btn" data-act="toggle-album" data-id="${album.id}" aria-expanded="${!collapsed}" title="${collapsed ? 'Expandir' : 'Contraure'}">
              <span class="chev ${collapsed ? 'is-closed' : ''}">${icon('chevron')}</span>
          </button>
          ${cover}
          <div class="album-meta">
              <span class="kicker">Àlbum · ${album.tracks.length} pistes · ${doneCount} llestes ${album.status === "OBERT" ? `<span class="badge badge-warning" style="margin-left: 8px;">OBERT</span>` : `<span class="badge badge-success" style="margin-left: 8px;">TANCAT</span>`}</span>
              <h3 class="album-title">${esc(album.title)}</h3>
          </div>
          <div class="album-actions">
              <button class="btn btn-ghost btn-sm" data-act="play-album" data-id="${album.id}" ${doneCount ? '' : 'disabled'}>${icon('play')} Reproduir</button>
              <button class="btn btn-ghost btn-sm" data-act="add-to-album" data-id="${album.id}" data-title="${esc(album.title)}" title="Afegir pistes a aquest àlbum">${icon("plus")} Afegir</button>
              <button class="btn btn-ghost btn-sm" data-act="export-album" data-format="mp3" data-id="${album.id}" ${doneCount ? '' : 'disabled'}>${icon('download')} ZIP MP3</button>
              <button class="btn btn-ghost btn-sm" data-act="export-album" data-format="mp4" data-id="${album.id}" ${doneCount ? '' : 'disabled'}>${icon('download')} ZIP MP4</button>
                <button class="btn btn-ghost btn-sm" data-act="export-album" data-format="yt" data-id="${album.id}" ${doneCount ? '' : 'disabled'} title="Exporta un sol vídeo per pujar-lo a YouTube">${icon('youtube')} Vídeo YouTube</button>
              <button class="icon-btn" data-act="rename-album" data-id="${album.id}" title="Canviar el nom de l'àlbum">${icon('rename')}</button>
              <button class="icon-btn danger" data-act="delete-album" data-id="${album.id}" title="Esborrar l'àlbum">${icon('trash')}</button>
          </div>
      </header>
      <ol class="album-tracks" ${collapsed ? 'hidden' : ''}>
          ${album.tracks.map((t, i) => trackRow(t, album, i + 1)).join('')}
      </ol>
  </section>`;
}

function renderLibrary() {
  const data = ui.library;
  const holder = $('libraryContainer');
  const albums = data.albums.map(albumCard).join('');
  const singles = data.singles.length
    ? `<section class="album">
          <header class="album-head">
              <span class="album-cover-ph">${icon('track')}</span>
              <div class="album-meta"><span class="kicker">Pistes soltes</span><h3 class="album-title">Singles</h3></div>
          </header>
          <ul class="album-tracks">${data.singles.map(t => trackRow(t, null, null)).join('')}</ul>
      </section>`
    : '';
  holder.innerHTML = (albums + singles) || `<div class="library-empty">${icon('library')}<strong>Encara no hi ha música</strong><span>Les pistes que generis apareixeran aquí.</span></div>`;
}

// ----- Reproductor -----
const player = { queue: [], index: -1 };

function playQueue(items, start = 0) {
  player.queue = items.filter(i => i.filepath).map(i => ({ id: i.id, title: i.title, url: i.filepath }));
  if (!player.queue.length) return toast('No hi ha cap pista reproduïble', 'warning');
  player.index = clamp(start, 0, player.queue.length - 1);
  loadPlayerItem(true);
}

function loadPlayerItem(autoplay) {
  const item = player.queue[player.index];
  const audio = $('player');
  audio.src = item.url;
  $('playerTitle').textContent = item.title;
  $('playerBar').hidden = false;
  if (autoplay) audio.play().catch(() => {});
  updatePlayIcon();
}

function updatePlayIcon() {
  const audio = $('player');
  $('btnPlayPause').innerHTML = audio.paused ? icon('play') : icon('pause');
}

function togglePlay() {
  const audio = $('player');
  if (!audio.src) return;
  audio.paused ? audio.play() : audio.pause();
}

function playNext() {
  if (player.index + 1 < player.queue.length) { player.index++; loadPlayerItem(true); }
}

function playPrev() {
  const audio = $('player');
  if (audio.currentTime > 3 || player.index === 0) { audio.currentTime = 0; return; }
  player.index--;
  loadPlayerItem(true);
}

function closePlayer() {
  const audio = $('player');
  audio.pause();
  audio.removeAttribute('src');
  player.queue = [];
  player.index = -1;
  $('playerBar').hidden = true;
}

// ----- Accions de la biblioteca -----
async function exportAlbum(id, format) {
  const album = findAlbum(id);
  try {
    const data = await api(`/api/albums/${id}/export`, { method: 'POST', body: { format } });
    trackJob(data.job_id, `ZIP ${format.toUpperCase()} · ${album ? album.title : 'Àlbum'}`, (job) => {
      downloadUrl(job.result.download_url);
    });
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function renameAlbum(id) {
  const album = findAlbum(id);
  const title = await askText("Nou nom de l'àlbum", album ? album.title : '');
  if (!title) return;
  try {
    await api(`/api/albums/${id}`, { method: 'PATCH', body: { title } });
    loadLibrary();
  } catch (e) { toast(e.message, 'error'); }
}

async function renameTrack(id) {
  const track = findTrack(id);
  const title = await askText('Nou nom de la pista', track ? track.title : '');
  if (!title) return;
  try {
    await api(`/api/tracks/${id}`, { method: 'PATCH', body: { title } });
    loadLibrary();
  } catch (e) { toast(e.message, 'error'); }
}

async function deleteTrack(id) {
  const ok = await askConfirm('Vols esborrar aquesta pista? Aquesta acció no es pot desfer.', 'Esborrar', true);
  if (!ok) return;
  await api(`/api/tracks/${id}`, { method: 'DELETE' });
  loadLibrary();
}

async function deleteAlbum(id) {
  const ok = await askConfirm("Vols esborrar l'àlbum sencer i tots els seus arxius?", 'Esborrar àlbum', true);
  if (!ok) return;
  await api(`/api/albums/${id}`, { method: 'DELETE' });
  loadLibrary();
}

// ===================== Editor de cançó =====================
const EXAMPLE_INSTRUCTIONS = ['Afegeix violins.', 'Treure el piano.', 'Més percussió.', 'Fes-ho més tranquil.', 'Crescendo.'];
const OP_LABELS = { regenerate: 'Regenerada', modify: 'Regions modificades', extend: 'Allargada' };

async function openEditor(trackId) {
  const track = findTrack(trackId);
  let state;
  try {
    state = await api(`/api/tracks/${trackId}/edit`);
  } catch (e) {
    return toast(e.message, 'error');
  }
  ui.editor = { trackId, title: track ? track.title : '', state, regions: [], selectedId: null, drag: null, polling: null, wasBusy: state.busy };

  showOverlay(`
      <div class="editor">
          <div class="dialog-head">
              <div><span class="kicker">Editor de cançó ${album.status === "OBERT" ? `<span class="badge badge-warning" style="margin-left: 8px;">OBERT</span>` : `<span class="badge badge-success" style="margin-left: 8px;">TANCAT</span>`}</span><h3 id="edTitle"></h3></div>
              <button class="icon-btn" id="edClose" title="Tancar (l'edició es manté)">${icon('close')}</button>
          </div>
          <div class="editor-toolbar">
              <div class="btn-group">
                  <button class="btn btn-ghost btn-sm" id="edUndo" title="Ctrl+Z">${icon('undo')} Desfer</button>
                  <button class="btn btn-ghost btn-sm" id="edRedo" title="Ctrl+Y">${icon('redo')} Refer</button>
              </div>
              <div class="btn-group">
                  <button class="btn btn-ghost btn-sm" id="edCancel">${icon('close')} Cancel·lar</button>
                  <button class="btn btn-primary btn-sm" id="edConfirm">${icon('check')} Confirmar</button>
              </div>
          </div>
          <div class="wave-wrap" id="edWaveWrap">
              <canvas id="edCanvas" class="wave"></canvas>
              <div id="edPopover" class="region-popover" hidden></div>
          </div>
          <div class="transport">
              <button class="icon-btn" id="edPlay" title="Reproduir"></button>
              <span class="mono muted" id="edTime">0:00 / 0:00</span>
              <span class="muted small">Arrossega sobre la forma d'ona per marcar una regió.</span>
          </div>
          <audio id="edAudio" preload="auto"></audio>

          <div class="editor-grid">
              <section class="op-card">
                  <header><h4>Modificar per regions</h4><span class="badge badge-warning">Experimental</span></header>
                  <div class="warning-note">${esc(state.warnings.experimental)}</div>
                  <ul class="region-list" id="edRegionList"></ul>
                  <button class="btn btn-ghost btn-block" id="edApplyModify">${icon('modify')} Aplicar modificació</button>
              </section>
              <section class="op-card">
                  <header><h4>Regenerar-ho tot</h4></header>
                  <textarea id="edRegenText" class="field" rows="3" placeholder="Què vols canviar? Ex: Afegeix piano. Fes l'inici minimalista."></textarea>
                  <div class="warning-note">${esc(state.warnings.regenerate)}</div>
                  <button class="btn btn-ghost btn-block" id="edApplyRegen">${icon('regen')} Regenerar</button>
              </section>
              <section class="op-card">
                  <header><h4>Allargar</h4></header>
                  <label class="label" for="edExtendSecs">Afegir (segons, màxim ${state.max_generation_seconds})</label>
                  <input type="number" id="edExtendSecs" class="field" value="10" min="1" max="${state.max_generation_seconds}">
                  <label class="label" for="edExtendText">Instrucció (opcional)</label>
                  <input type="text" id="edExtendText" class="field" placeholder="Ex: mantén el mateix ritme">
                  <button class="btn btn-ghost btn-block" id="edApplyExtend">${icon('extend')} Allargar el final</button>
              </section>
          </div>

          <section class="versions">
              <h4>Versions</h4>
              <ol class="version-list" id="edVersions"></ol>
          </section>
          <p class="status-line muted" id="edStatus"></p>
      </div>`, 'dialog-lg');

  bindEditor();
  refreshEditor();
  document.addEventListener('keydown', editorKeys);
}

function bindEditor() {
  const ed = ui.editor;
  const canvas = $('edCanvas');

  $('edClose').onclick = closeEditor;
  $('edUndo').onclick = () => editorAction('undo');
  $('edRedo').onclick = () => editorAction('redo');
  $('edConfirm').onclick = confirmEditor;
  $('edCancel').onclick = cancelEditor;
  $('edApplyRegen').onclick = () => {
    const instruction = $('edRegenText').value.trim();
    if (!instruction) return toast('Escriu què vols canviar', 'warning');
    editorRequest(`/api/tracks/${ed.trackId}/edit/regenerate`, { instruction });
  };
  $('edApplyExtend').onclick = () => editorRequest(`/api/tracks/${ed.trackId}/edit/extend`, {
    seconds: parseInt($('edExtendSecs').value, 10),
    instruction: $('edExtendText').value.trim(),
  });
  $('edApplyModify').onclick = () => {
    const missing = ed.regions.find(r => !r.instruction);
    if (!ed.regions.length) return toast('Marca almenys una regió a la forma d\'ona', 'warning');
    if (missing) return toast('Cada regió necessita una instrucció', 'warning');
    editorRequest(`/api/tracks/${ed.trackId}/edit/modify`, {
      annotations: ed.regions.map(r => ({ startTime: r.startTime, endTime: r.endTime, instruction: r.instruction })),
    });
  };
  $('edPlay').onclick = () => {
    const audio = $('edAudio');
    audio.paused ? audio.play() : audio.pause();
  };
  $('edAudio').addEventListener('timeupdate', updateEditorTransport);
  $('edAudio').addEventListener('play', () => { $('edPlay').innerHTML = icon('pause'); });
  $('edAudio').addEventListener('pause', () => { $('edPlay').innerHTML = icon('play'); });

  canvas.addEventListener('pointerdown', (e) => {
    if (ed.state.busy) return;
    const t = editorTime(e);
    const dur = ed.state.duration;
    const tol = (8 / canvas.clientWidth) * dur;
    const selected = ed.regions.find(r => r.id === ed.selectedId);
    hidePopover();
    if (selected && Math.abs(t - selected.startTime) <= tol) {
      ed.drag = { mode: 'resize', id: selected.id, edge: 'start' };
    } else if (selected && Math.abs(t - selected.endTime) <= tol) {
      ed.drag = { mode: 'resize', id: selected.id, edge: 'end' };
    } else {
      const hit = ed.regions.find(r => t >= r.startTime && t <= r.endTime);
      if (hit) {
        ed.selectedId = hit.id;
        ed.drag = null;
        refreshEditorWave();
        renderRegionList();
        showPopover(hit);
        return;
      }
      const region = { id: `r${Date.now()}${Math.random().toString(16).slice(2, 6)}`, startTime: t, endTime: t, instruction: '' };
      ed.regions.push(region);
      ed.selectedId = region.id;
      ed.drag = { mode: 'create', id: region.id, anchor: t };
    }
    canvas.setPointerCapture(e.pointerId);
    refreshEditorWave();
  });

  canvas.addEventListener('pointermove', (e) => {
    if (!ed.drag) return;
    const region = ed.regions.find(r => r.id === ed.drag.id);
    if (!region) return;
    const t = clamp(editorTime(e), 0, ed.state.duration);
    let start = region.startTime;
    let end = region.endTime;
    if (ed.drag.mode === 'create') {
      start = Math.min(ed.drag.anchor, t);
      end = Math.max(ed.drag.anchor, t);
    } else if (ed.drag.edge === 'start') {
      start = Math.min(t, region.endTime - 0.5);
    } else {
      end = Math.max(t, region.startTime + 0.5);
    }
    if (!overlapsOther(region, start, end)) {
      region.startTime = Math.max(0, start);
      region.endTime = Math.min(ed.state.duration, end);
    }
    refreshEditorWave();
  });

  const finishDrag = () => {
    if (!ed.drag) return;
    const region = ed.regions.find(r => r.id === ed.drag.id);
    ed.drag = null;
    if (!region) return;
    if (region.endTime - region.startTime < 0.5) {
      ed.regions = ed.regions.filter(r => r !== region);
      ed.selectedId = null;
      toast('La regió és massa curta (mínim 0,5 s)', 'warning');
    } else {
      showPopover(region);
    }
    refreshEditorWave();
    renderRegionList();
  };
  canvas.addEventListener('pointerup', finishDrag);
  canvas.addEventListener('pointercancel', finishDrag);
  window.addEventListener('resize', refreshEditorWave);
}

function overlapsOther(region, start, end) {
  return ui.editor.regions.some(r => r !== region && start < r.endTime && end > r.startTime);
}

function editorTime(e) {
  const canvas = $('edCanvas');
  const rect = canvas.getBoundingClientRect();
  return ((e.clientX - rect.left) / rect.width) * ui.editor.state.duration;
}

function editorKeys(e) {
  if (!ui.editor) return;
  const tag = (document.activeElement && document.activeElement.tagName) || '';
  if (['INPUT', 'TEXTAREA', 'SELECT'].includes(tag)) return;
  if ((e.ctrlKey || e.metaKey) && !e.shiftKey && e.key.toLowerCase() === 'z') { e.preventDefault(); editorAction('undo'); }
  if (((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'y') || ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 'z')) {
    e.preventDefault();
    editorAction('redo');
  }
}

function showPopover(region) {
  const ed = ui.editor;
  ed.selectedId = region.id;
  const pop = $('edPopover');
  const canvas = $('edCanvas');
  const w = canvas.clientWidth;
  const centre = ((region.startTime + region.endTime) / 2 / ed.state.duration) * w;
  const left = clamp(centre - 150, 8, Math.max(8, w - 308));
  pop.style.left = `${left}px`;
  pop.innerHTML = `
      <strong class="small">Què vols canviar aquí?</strong>
      <span class="muted small">${fmtTime(region.startTime)} – ${fmtTime(region.endTime)}</span>
      <textarea class="field field-sm" id="popText" rows="2" placeholder="Ex: Afegeix violins.">${esc(region.instruction)}</textarea>
      <div class="examples">${EXAMPLE_INSTRUCTIONS.map(x => `<button type="button" data-ex="${esc(x)}">${esc(x)}</button>`).join('')}</div>
      <div class="row">
          <button class="btn btn-ghost btn-sm" id="popRemove">${icon('trash')} Treure</button>
          <button class="btn btn-primary btn-sm" id="popSave">Desar regió</button>
      </div>`;
  pop.hidden = false;
  pop.querySelectorAll('[data-ex]').forEach(b => b.addEventListener('click', () => { $('popText').value = b.dataset.ex; }));
  $('popSave').onclick = () => {
    const text = $('popText').value.trim();
    if (!text) return toast('Escriu una instrucció per a la regió', 'warning');
    region.instruction = text;
    hidePopover();
    renderRegionList();
  };
  $('popRemove').onclick = () => {
    ui.editor.regions = ui.editor.regions.filter(r => r !== region);
    ui.editor.selectedId = null;
    hidePopover();
    refreshEditorWave();
    renderRegionList();
  };
  refreshEditorWave();
}

function hidePopover() {
  const pop = $('edPopover');
  if (pop) pop.hidden = true;
}

function renderRegionList() {
  const ed = ui.editor;
  if (!ed) return;
  $('edRegionList').innerHTML = ed.regions.length
    ? ed.regions.map(r => `<li data-region="${r.id}" class="${r.id === ed.selectedId ? 'is-selected' : ''}">
          <span class="mono">${fmtTime(r.startTime)}–${fmtTime(r.endTime)}</span>
          <span class="txt">${r.instruction ? esc(r.instruction) : '<em>Falta la instrucció</em>'}</span>
      </li>`).join('')
    : '<li><span class="muted">Cap regió marcada.</span></li>';
  $('edRegionList').querySelectorAll('li[data-region]').forEach(li => {
    li.addEventListener('click', () => {
      const region = ed.regions.find(r => r.id === li.dataset.region);
      if (region) { ed.selectedId = region.id; refreshEditorWave(); showPopover(region); }
    });
  });
}

function refreshEditorWave() {
  const ed = ui.editor;
  if (!ed) return;
  const canvas = $('edCanvas');
  if (!canvas) return;
  drawWave(canvas, ed.state.peaks, {
    duration: ed.state.duration,
    regions: ed.regions,
    selectedId: ed.selectedId,
    playhead: $('edAudio').currentTime || 0,
  });
  updateEditorTransport();
}

function updateEditorTransport() {
  const ed = ui.editor;
  if (!ed || !$('edTime')) return;
  $('edTime').textContent = `${fmtTime($('edAudio').currentTime)} / ${fmtTime(ed.state.duration)}`;
  redrawEditorPlayhead();
}

function redrawEditorPlayhead() {
  const ed = ui.editor;
  if (!ed || ed.drag) return;
  const canvas = $('edCanvas');
  if (!canvas) return;
  drawWave(canvas, ed.state.peaks, {
    duration: ed.state.duration,
    regions: ed.regions,
    selectedId: ed.selectedId,
    playhead: $('edAudio').currentTime || 0,
  });
}

function refreshEditor() {
  const ed = ui.editor;
  if (!ed) return;
  const s = ed.state;
  $('edTitle').textContent = ed.title || 'Pista';
  $('edUndo').disabled = s.busy || !s.can_undo;
  $('edRedo').disabled = s.busy || !s.can_redo;
  $('edConfirm').disabled = s.busy;
  $('edCancel').disabled = s.busy;
  ['edApplyModify', 'edApplyRegen', 'edApplyExtend'].forEach(id => { $(id).disabled = s.busy; });

  const audio = $('edAudio');
  if (audio.dataset.src !== s.active_url) {
    audio.dataset.src = s.active_url;
    audio.src = s.active_url;
  }
  $('edStatus').textContent = s.busy ? 'Processant una operació... pots tancar la finestra i tornar-hi més tard.' : '';

  const items = [{ id: null, label: 'Original', detail: '', status: 'done', active: s.active_revision_id === null, error: null }]
    .concat(s.revisions.map(r => ({ id: r.id, label: OP_LABELS[r.operation] || r.operation, detail: r.instruction || '', status: r.status, active: r.is_active, error: r.error_msg })));
  $('edVersions').innerHTML = items.map(v => {
    const badge = v.status === 'error' ? '<span class="badge badge-error">Error</span>'
      : v.status === 'done' ? (v.active ? '<span class="badge badge-accent">Activa</span>' : '')
        : '<span class="badge badge-warning"><span class="spinner"></span>En curs</span>';
    return `<li class="${v.active ? 'is-active' : ''}" title="${esc(v.error || '')}">
        <strong>${esc(v.label)}</strong>${v.detail ? `<span class="muted">${esc(v.detail)}</span>` : ''}${badge}
    </li>`;
  }).join('');

  renderRegionList();
  refreshEditorWave();
  if (s.busy) {
    scheduleEditorPoll();
  } else if (ed.wasBusy) {
    ed.wasBusy = false;
    const failed = s.revisions.find(r => r.status === 'error' && !r.is_active);
    if (failed) toast(`L'operació ha fallat: ${failed.error_msg || 'error desconegut'}`, 'error');
    else toast('Nova versió creada', 'success');
  }
  ed.wasBusy = s.busy;
}

function scheduleEditorPoll() {
  const ed = ui.editor;
  if (!ed) return;
  clearTimeout(ed.polling);
  ed.polling = setTimeout(async () => {
    if (!ui.editor || ui.editor !== ed) return;
    try {
      ed.state = await api(`/api/tracks/${ed.trackId}/edit`);
      refreshEditor();
    } catch (e) {
      toast(e.message, 'error');
    }
  }, 1500);
}

async function editorRequest(url, body) {
  const ed = ui.editor;
  try {
    const data = await api(url, { method: 'POST', body });
    ed.state = data.state;
    ed.regions = [];
    ed.selectedId = null;
    hidePopover();
    ed.wasBusy = true;
    refreshEditor();
    toast('Operació iniciada', 'info');
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function editorAction(action) {
  const ed = ui.editor;
  if (!ed || ed.state.busy) return;
  try {
    const data = await api(`/api/tracks/${ed.trackId}/edit/${action}`, { method: 'POST' });
    ed.state = data.state;
    refreshEditor();
  } catch (e) {
    toast(e.message, 'warning');
  }
}

async function confirmEditor() {
  const ok = await askConfirm("Confirmar la versió activa? S'eliminaran les altres versions i l'historial d'edició.", 'Confirmar');
  if (!ok) return;
  const trackId = ui.editor.trackId;
  try {
    await api(`/api/tracks/${trackId}/edit/confirm`, { method: 'POST' });
    toast('Versió confirmada com a àudio principal', 'success');
    closeEditor(true);
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function cancelEditor() {
  const ok = await askConfirm("Cancel·lar l'edició? Es restaurarà l'original i es perdran les revisions.", 'Cancel·lar edició', true);
  if (!ok) return;
  const trackId = ui.editor.trackId;
  try {
    await api(`/api/tracks/${trackId}/edit/cancel`, { method: 'POST' });
    toast("Edició cancel·lada. L'original no ha canviat", 'info');
    closeEditor(true);
  } catch (e) {
    toast(e.message, 'error');
  }
}

function closeEditor(reload = false) {
  if (ui.editor) clearTimeout(ui.editor.polling);
  document.removeEventListener('keydown', editorKeys);
  const audio = document.getElementById('edAudio');
  if (audio) audio.pause();
  ui.editor = null;
  closeOverlay();
  if (reload) loadLibrary();
}

// ===================== Navegació i inicialització =====================
function switchTab(tab) {
  document.querySelectorAll('.tab').forEach(b => {
    const active = b.dataset.tab === tab;
    b.classList.toggle('active', active);
    b.setAttribute('aria-selected', String(active));
  });
  $('view-gen').hidden = tab !== 'gen';
  $('view-lib').hidden = tab !== 'lib';
  if (tab === 'lib') loadLibrary();
}

function bindEvents() {

  document.getElementById('view-gen').addEventListener('input', (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') {
      updateYTPreview();
    }
  });
  document.getElementById('view-gen').addEventListener('change', (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') {
      updateYTPreview();
    }
  });

  
  document.querySelectorAll('.tab').forEach(b => b.addEventListener('click', () => switchTab(b.dataset.tab)));

  $('title').addEventListener('input', () => {
    if (ui.targetAlbumId && $('title').value !== ui.targetAlbumTitle) {
      ui.targetAlbumId = null;
      ui.targetAlbumTitle = null;
      applyAlbumMode();
    }
  });

  $('modeAlbumToggle').addEventListener('change', (e) => {
    ui.albumOn = e.target.checked;
    applyAlbumMode();
  });
  
  document.querySelectorAll('#albumModeSeg button').forEach(b => b.addEventListener('click', () => {
    ui.albumMode = b.dataset.mode;
    applyAlbumMode();
    updateYTPreview();
  }));
  $('manualCount').addEventListener('change', (e) => {
    const n = clamp(parseInt(e.target.value, 10) || 1, 1, 20);
    e.target.value = n;
    if (ui.albumOn && ui.albumMode === 'manual') setBlockCount(n);
  });
  $('sameInstruments').addEventListener('change', () => {
    $('instrumentGrid').closest('.instruments').hidden = ui.albumOn && ui.albumMode === 'manual' && !$('sameInstruments').checked;
    refreshBlocks();
  updateYTPreview();
  });
  $('comfyModelSelect').addEventListener('change', updateDeleteBtn);
  $('btnDeleteModel').addEventListener('click', deleteComfyModel);
  $('btnUploadCover').addEventListener('click', () => $('coverInput').click());
  $('coverInput').addEventListener('change', (e) => uploadCover(e.target));
  $('btnComfyUI').addEventListener('click', generateCoverComfyUI);
  $('submitBtn').addEventListener('click', submitJob);
  $('btnRefreshLib').addEventListener('click', loadLibrary);

  document.querySelectorAll('#inspTabs button').forEach(b => b.addEventListener('click', () => {
    ui.inspTab = b.dataset.tab;
    renderInspirations();
  }));

  $('inspContent').addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-act]');
    if (!btn) return;
    const id = btn.dataset.id;
    if (btn.dataset.act === 'pick-file') return $('inspFile').click();
    if (btn.dataset.act === 'use-insp') return activateInspiration(id);
    if (btn.dataset.act === 'fav-insp') {
      await api(`/api/inspirations/${id}/favorite`, { method: 'POST', body: { favorite: btn.dataset.fav === 'true' } });
      return loadInspirations();
    }
    if (btn.dataset.act === 'del-insp') {
      const ok = await askConfirm("Esborrar aquesta inspiració de la biblioteca?", 'Esborrar', true);
      if (!ok) return;
      if (ui.activeInsp && ui.activeInsp.id === id) ui.activeInsp = null;
      await api(`/api/inspirations/${id}`, { method: 'DELETE' });
      return loadInspirations();
    }
  });
  $('inspContent').addEventListener('change', async (e) => {
    if (e.target.id === 'cleanupSelect') {
      try {
        await api('/api/settings/inspiration-cleanup', { method: 'POST', body: { days: parseInt(e.target.value, 10) } });
        toast('Política de neteja actualitzada', 'success');
        loadInspirations();
      } catch (err) { toast(err.message, 'error'); }
    }
    if (e.target.id === 'inspFile' && e.target.files.length) {
      importLocal(e.target.files[0]).catch(err => toast(err.message, 'error'));
      e.target.value = '';
    }
  });
  $('inspContent').addEventListener('submit', (e) => {
    if (e.target.id !== 'ytForm') return;
    e.preventDefault();
    const url = $('ytUrl').value.trim();
    if (!url) return toast('Escriu un enllaç de YouTube', 'warning');
    importYoutube(url).catch(err => toast(err.message, 'error'));
    $('ytUrl').value = '';
  });
  $('activeInspiration').addEventListener('click', (e) => {
    if (e.target.closest('[data-act="clear-insp"]')) {
      ui.activeInsp = null;
      renderActiveInspiration();
      renderInspirations();
    }
  });

  $('libraryContainer').addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-act]');
    if (!btn) return;
    const id = btn.dataset.id;
    try {
      switch (btn.dataset.act) {
        case 'toggle-album':
          ui.collapsed.has(id) ? ui.collapsed.delete(id) : ui.collapsed.add(id);
          return renderLibrary();
        case 'add-to-album':
          ui.targetAlbumId = id;
          ui.targetAlbumTitle = btn.dataset.title;
          $('modeAlbumToggle').checked = true;
          ui.albumOn = true;
          $('title').value = ui.targetAlbumTitle;
          applyAlbumMode();
    updateYTPreview();
          return switchTab('gen');
        case 'play-track':
          return playQueue([findTrack(id)]);
        case 'play-album': {
          const album = findAlbum(id);
          return playQueue(album ? album.tracks : []);
        }
        case 'export-album':
          return exportAlbum(id, btn.dataset.format);
        case 'rename-album':
          return renameAlbum(id);
        case 'delete-album':
          return deleteAlbum(id);
        case 'rename-track':
          return renameTrack(id);
        case 'delete-track':
          return deleteTrack(id);
        case 'edit-track':
          return openEditor(id);
      }
    } catch (err) {
      toast(err.message, 'error');
    }
  });

  const audio = $('player');
  audio.addEventListener('play', updatePlayIcon);
  audio.addEventListener('pause', updatePlayIcon);
  audio.addEventListener('ended', playNext);
  audio.addEventListener('timeupdate', () => {
    const dur = audio.duration || 0;
    $('playerSeek').value = dur ? Math.round((audio.currentTime / dur) * 1000) : 0;
    $('playerTime').textContent = `${fmtTime(audio.currentTime)} / ${fmtTime(dur)}`;
  });
  $('playerSeek').addEventListener('input', (e) => {
    const dur = audio.duration || 0;
    audio.currentTime = (e.target.value / 1000) * dur;
  });
  $('btnPlayPause').addEventListener('click', togglePlay);
  $('btnNext').addEventListener('click', playNext);
  $('btnPrev').addEventListener('click', playPrev);
  $('btnClosePlayer').addEventListener('click', closePlayer);
}

window.addEventListener('DOMContentLoaded', () => {
  hydrateIcons();
  renderWizard($('instrumentGrid'), globalStates, null, false);
  $('instrumentGrid').closest('.instruments').hidden = false;
  bindEvents();
  setBlockCount(1);
  $('manualCount').value = 1;
  pollQueue();
  loadComfyModels();
  loadInspirations();
  $('overlay').addEventListener('click', (e) => {
    if (e.target.id === 'overlay' && !ui.editor && !document.querySelector('#overlayCard .selector-meta')) closeOverlay();
  });
});

setTimeout(updateYTPreview, 500);
