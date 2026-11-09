import { env, pipeline } from '@huggingface/transformers';

env.useBrowserCache = true;
env.useWasmCache = true;
env.cacheKey = 'quick-t-mobile-models';

const pipelines = new Map();

function sendStatus(text) {
  self.postMessage({ type: 'status', text });
}

async function createPipeline(model, preferWebGPU) {
  const key = `${model}:${preferWebGPU ? 'webgpu' : 'wasm'}`;
  if (pipelines.has(key)) return pipelines.get(key);

  const progress_callback = (event) => {
    if (event.status === 'progress_total') {
      self.postMessage({
        type: 'progress',
        text: 'Téléchargement du modèle…',
        progress: event.progress,
      });
    } else if (event.status === 'initiate') {
      sendStatus('Préparation du modèle local…');
    }
  };

  const options = { dtype: 'q8', progress_callback };
  if (preferWebGPU) options.device = 'webgpu';
  const instance = await pipeline('automatic-speech-recognition', model, options);
  pipelines.set(key, instance);
  return instance;
}

self.addEventListener('message', async (event) => {
  const { type, audio, mimeType, model, language, hasWebGPU } = event.data ?? {};
  if (type !== 'transcribe') return;

  let engine = 'CPU';
  try {
    let transcriber;
    if (hasWebGPU) {
      try {
        sendStatus('Activation de l’accélération disponible…');
        transcriber = await createPipeline(model, true);
        engine = 'WebGPU';
      } catch (gpuError) {
        console.warn('Accélération indisponible, repli sur le moteur compatible.', gpuError);
        sendStatus('Mode compatible activé…');
        transcriber = await createPipeline(model, false);
      }
    } else {
      transcriber = await createPipeline(model, false);
    }

    sendStatus('Transcription en cours… garde l’app ouverte.');
    const blobUrl = URL.createObjectURL(new Blob([audio], { type: mimeType }));
    try {
      const options = { chunk_length_s: 30, stride_length_s: 5 };
      if (language !== 'auto') options.language = language;
      const result = await transcriber(blobUrl, options);
      self.postMessage({ type: 'result', text: result.text || '', engine });
    } finally {
      URL.revokeObjectURL(blobUrl);
    }
  } catch (error) {
    self.postMessage({ type: 'error', message: error?.message || 'Une erreur inconnue est survenue.' });
  }
});
