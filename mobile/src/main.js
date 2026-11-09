import './style.css';

const DB_NAME = 'quick-t-mobile';
const DB_VERSION = 1;
const STORE_NAME = 'transcriptions';

const fileInput = document.querySelector('#audio-file');
const youtubeUrl = document.querySelector('#youtube-url');
const youtubeError = document.querySelector('#youtube-error');
const sessionBox = document.querySelector('#session-box');
const sessionCode = document.querySelector('#session-code');
const fileName = document.querySelector('#file-name');
const transcribeButton = document.querySelector('#transcribe-button');
const speedMode = document.querySelector('#speed-mode');
const language = document.querySelector('#language');
const progressArea = document.querySelector('#progress-area');
const progressBar = document.querySelector('#progress-bar');
const statusText = document.querySelector('#status-text');
const progressValue = document.querySelector('#progress-value');
const resultCard = document.querySelector('#result-card');
const transcript = document.querySelector('#transcript');
const storedLocation = document.querySelector('#stored-location');
const historyCard = document.querySelector('#history-card');
const historyList = document.querySelector('#history-list');
const installButton = document.querySelector('#install-button');
const installHint = document.querySelector('#install-hint');

let selectedFile = null;
let currentSourceName = "audio";
let sessionToken = localStorage.getItem("quick-t-link-token") || "";
const urlToken = new URLSearchParams(location.hash.slice(1)).get("key");
if (urlToken) {
  sessionToken = urlToken;
  localStorage.setItem("quick-t-link-token", sessionToken);
  history.replaceState(null, "", location.pathname + location.search);
}
sessionCode.value = sessionToken;
sessionBox.hidden = Boolean(sessionToken);
let currentRecord = null;
let installPrompt = null;
let activeWorker = null;

const worker = new Worker(new URL('./transcriber.worker.js', import.meta.url), { type: 'module' });

function setStatus(text, progress = null) {
  statusText.textContent = text;
  if (progress === null) {
    progressBar.removeAttribute('value');
    progressValue.textContent = '';
  } else {
    progressBar.value = Math.max(0, Math.min(100, progress));
    progressValue.textContent = `${Math.round(progressBar.value)} %`;
  }
}

function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'id' });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error || new Error('Stockage local indisponible.'));
  });
}

async function saveRecord(record) {
  const db = await openDatabase();
  try {
    await new Promise((resolve, reject) => {
      const transaction = db.transaction(STORE_NAME, 'readwrite');
      transaction.objectStore(STORE_NAME).put(record);
      transaction.oncomplete = resolve;
      transaction.onerror = () => reject(transaction.error || new Error('Impossible d’enregistrer la transcription.'));
      transaction.onabort = () => reject(transaction.error || new Error('Enregistrement interrompu.'));
    });
  } finally {
    db.close();
  }
}

async function readRecords() {
  const db = await openDatabase();
  try {
    return await new Promise((resolve, reject) => {
      const request = db.transaction(STORE_NAME, 'readonly').objectStore(STORE_NAME).getAll();
      request.onsuccess = () => resolve(request.result.sort((a, b) => b.createdAt - a.createdAt));
      request.onerror = () => reject(request.error || new Error('Impossible de lire l’historique.'));
    });
  } finally {
    db.close();
  }
}

function makeOutputName(inputName) {
  const base = (inputName || 'transcription')
    .replace(/\.[^.]+$/, '')
    .replace(/[\\/*?:"<>|\x00-\x1f]/g, '_')
    .trim()
    .replace(/\s+/g, '_')
    .slice(0, 120) || 'transcription';
  return `${base}.txt`;
}

function formatDate(timestamp) {
  return new Intl.DateTimeFormat('fr-FR', { dateStyle: 'medium', timeStyle: 'short' }).format(timestamp);
}

async function refreshHistory() {
  try {
    const records = await readRecords();
    historyList.replaceChildren();
    historyCard.hidden = records.length === 0;
    for (const record of records) {
      const row = document.createElement('article');
      row.className = 'history-item';
      const meta = document.createElement('div');
      meta.className = 'history-meta';
      const name = document.createElement('strong');
      name.className = 'history-name';
      name.textContent = record.outputName;
      const date = document.createElement('small');
      date.className = 'history-date';
      date.textContent = formatDate(record.createdAt);
      meta.append(name, date);
      const openButton = document.createElement('button');
      openButton.className = 'button history-action';
      openButton.type = 'button';
      openButton.textContent = 'Ouvrir';
      openButton.addEventListener('click', () => showRecord(record));
      const exportButton = document.createElement('button');
      exportButton.className = 'button history-action history-export';
      exportButton.type = 'button';
      exportButton.textContent = 'Exporter';
      exportButton.addEventListener('click', () => exportRecord(record));
      row.append(meta, openButton, exportButton);
      historyList.append(row);
    }
  } catch (error) {
    historyCard.hidden = false;
    historyList.textContent = `Historique indisponible : ${error.message}`;
  }
}

function showRecord(record) {
  currentRecord = record;
  transcript.value = record.text;
  storedLocation.textContent = `Fichier : ${record.outputName}. Enregistré dans Quick T sur cet iPhone. Pour l’avoir dans l’app Fichiers, touche « Exporter / enregistrer dans Fichiers ».`;
  resultCard.hidden = false;
  resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function exportRecord(record) {
  const file = new File([`${record.text}\n`], record.outputName, { type: 'text/plain;charset=utf-8' });
  if (navigator.canShare?.({ files: [file] }) && navigator.share) {
    try {
      await navigator.share({ files: [file], title: record.outputName });
      return;
    } catch (error) {
      if (error.name === 'AbortError') return;
    }
  }
  const url = URL.createObjectURL(file);
  const link = document.createElement('a');
  link.href = url;
  link.download = record.outputName;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
}

function validYouTubeUrl(value) {
  if (!value) return false;
  try {
    const parsed = new URL(value);
    const host = parsed.hostname.toLowerCase().replace(/\.$/, '');
    return parsed.protocol === 'https:' &&
      (host === 'youtu.be' || host.endsWith('.youtu.be') || host === 'youtube.com' || host.endsWith('.youtube.com'));
  } catch {
    return false;
  }
}

function updateSourceAvailability() {
  const link = youtubeUrl.value.trim();
  const hasLink = Boolean(link);
  const validLink = validYouTubeUrl(link);
  let errorMessage = '';
  if (hasLink && !validLink) {
    errorMessage = 'Colle un lien YouTube HTTPS valide (youtube.com ou youtu.be).';
  } else if (hasLink && !sessionToken) {
    errorMessage = 'Colle le code temporaire de test reçu dans le chat.';
  }
  youtubeError.hidden = !errorMessage;
  youtubeError.textContent = errorMessage;
  sessionBox.hidden = Boolean(sessionToken);
  transcribeButton.disabled = Boolean(activeWorker) || (hasLink ? (!validLink || !sessionToken) : !selectedFile);
}

sessionCode.addEventListener('input', () => {
  const value = sessionCode.value.trim();
  sessionToken = value.length >= 24 ? value : '';
  if (sessionToken) localStorage.setItem('quick-t-link-token', sessionToken);
  else localStorage.removeItem('quick-t-link-token');
  updateSourceAvailability();
});

youtubeUrl.addEventListener('input', () => {
  if (youtubeUrl.value.trim() && selectedFile) {
    selectedFile = null;
    fileInput.value = '';
    fileName.textContent = 'MP3, WAV, M4A ou autre format pris en charge';
  }
  updateSourceAvailability();
});

fileInput.addEventListener('change', () => {
  selectedFile = fileInput.files?.[0] ?? null;
  fileName.textContent = selectedFile ? selectedFile.name : 'MP3, WAV, M4A ou autre format pris en charge';
  if (selectedFile) youtubeUrl.value = '';
  updateSourceAvailability();
});

speedMode.addEventListener('change', () => {
  document.querySelector('#device-note').textContent = speedMode.value === 'fast'
    ? 'Profil léger : privilégie la vitesse et limite le stockage requis.'
    : 'Profil plus précis : téléchargement initial et calcul plus importants.';
});

async function getAudioSource() {
  const link = youtubeUrl.value.trim();
  if (link) {
    if (!validYouTubeUrl(link)) throw new Error('Colle un lien YouTube HTTPS valide.');
    if (!sessionToken) throw new Error('Code temporaire manquant. Colle le code reçu dans le chat.');
    setStatus('Récupération de l’audio YouTube par le Mac de test…');
    const response = await fetch('./api/youtube-audio', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${sessionToken}` },
      body: JSON.stringify({ url: link }),
    });
    if (!response.ok) {
      let message = `Erreur de récupération (${response.status}).`;
      try { message = (await response.json()).error || message; } catch { /* réponse non JSON */ }
      throw new Error(message);
    }
    const titleHeader = response.headers.get('X-Source-Title') || 'youtube_audio';
    let title = titleHeader;
    try { title = decodeURIComponent(titleHeader); } catch { /* garder le titre brut */ }
    currentSourceName = `${title}.mp3`;
    return { audio: await response.arrayBuffer(), mimeType: 'audio/mpeg' };
  }
  if (!selectedFile) throw new Error('Colle un lien YouTube ou choisis un fichier audio.');
  currentSourceName = selectedFile.name;
  return { audio: await selectedFile.arrayBuffer(), mimeType: selectedFile.type || 'audio/mpeg' };
}

transcribeButton.addEventListener('click', async () => {
  if (transcribeButton.disabled || activeWorker) return;
  activeWorker = worker;
  updateSourceAvailability();
  fileInput.disabled = true;
  youtubeUrl.disabled = true;
  speedMode.disabled = true;
  language.disabled = true;
  progressArea.hidden = false;
  resultCard.hidden = true;
  setStatus('Préparation…');

  try {
    if (navigator.storage?.persist) await navigator.storage.persist();
    const { audio, mimeType } = await getAudioSource();
    setStatus('Préparation du modèle sur cet iPhone…');
    worker.postMessage({
      type: 'transcribe',
      audio,
      mimeType,
      model: speedMode.value === 'fast' ? 'onnx-community/whisper-tiny' : 'onnx-community/whisper-base',
      language: language.value,
      hasWebGPU: Boolean(navigator.gpu),
    }, [audio]);
  } catch (error) {
    finishWithError(error);
  }
});

async function handleWorkerMessage(message) {
  if (message.type === 'status') setStatus(message.text);
  if (message.type === 'progress') setStatus(message.text, message.progress);
  if (message.type === 'result') {
    const record = {
      id: globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      sourceName: currentSourceName,
      outputName: makeOutputName(currentSourceName),
      text: message.text || '',
      createdAt: Date.now(),
    };
    transcript.value = record.text;
    currentRecord = record;
    resultCard.hidden = false;
    storedLocation.textContent = `Fichier : ${record.outputName}. Enregistrement dans Quick T sur cet iPhone…`;
    try {
      await saveRecord(record);
      storedLocation.textContent = `Fichier : ${record.outputName}. Enregistré dans Quick T sur cet iPhone. Pour l’avoir dans l’app Fichiers, touche « Exporter / enregistrer dans Fichiers ».`;
      setStatus(`Terminé et enregistré · ${message.engine}`);
      await refreshHistory();
    } catch (error) {
      storedLocation.textContent = `Fichier : ${record.outputName}. L’historique local n’a pas pu l’enregistrer (${error.message}). Exporte-le maintenant pour ne pas le perdre.`;
      setStatus('Transcription terminée, mais non enregistrée dans l’historique.');
    }
    resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
    finish();
  }
  if (message.type === 'error') finishWithError(new Error(message.message));
}

worker.addEventListener('message', (event) => { void handleWorkerMessage(event.data); });
worker.addEventListener('error', (event) => finishWithError(new Error(event.message || 'Erreur du moteur de transcription.')));

function finish() {
  activeWorker = null;
  fileInput.disabled = false;
  youtubeUrl.disabled = false;
  speedMode.disabled = false;
  language.disabled = false;
  updateSourceAvailability();
}

function finishWithError(error) {
  setStatus(`La transcription a échoué : ${error.message}`);
  finish();
}

document.querySelector('#copy-button').addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(transcript.value);
    document.querySelector('#copy-button').textContent = 'Copié';
    setTimeout(() => { document.querySelector('#copy-button').textContent = 'Copier'; }, 1600);
  } catch {
    transcript.focus();
    transcript.select();
    document.execCommand('copy');
  }
});

document.querySelector('#download-button').addEventListener('click', () => {
  if (currentRecord) void exportRecord(currentRecord);
});

window.addEventListener('beforeinstallprompt', (event) => {
  event.preventDefault();
  installPrompt = event;
  installButton.hidden = false;
});

installButton.addEventListener('click', async () => {
  if (!installPrompt) return;
  await installPrompt.prompt();
  installPrompt = null;
  installButton.hidden = true;
});

const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
const isStandalone = window.matchMedia('(display-mode: standalone)').matches || navigator.standalone;
if (isIOS && !isStandalone) {
  installHint.hidden = false;
  installHint.textContent = 'Pour installer l’app : ouvre le menu Partager de Safari, puis choisis « Sur l’écran d’accueil ». ';
}

void refreshHistory();
if ('serviceWorker' in navigator && location.protocol !== 'file:') {
  window.addEventListener('load', () => navigator.serviceWorker.register('./sw.js').catch(() => {}));
}
