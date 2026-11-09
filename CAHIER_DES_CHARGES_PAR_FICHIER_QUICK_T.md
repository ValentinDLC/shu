# Cahier des charges par fichier : Quick T

Date : 2026-11-09. Base : `develop` (a5d3e8b).

## Légende et méthode
- [C] constat visible dans le code lu (ligne indiquée). [H] hypothèse déduite de ma connaissance des bibliothèques et navigateurs, non testée.
- Aucun build, test ni essai sur appareil n'a été lancé pour écrire ce document.
- Non lus : `package-lock.json` (généré), icônes (binaires), cahiers.
- Les tâches `NOUV-xx` sont dans `CAHIER_DES_TACHES_QUICK_T.md` (provisoires, à valider).

## 0. Vue d'ensemble
- Bureau : `Quick_T.py` (CLI, openai-whisper) et `Quick_T_gui.py` (Tkinter, faster-whisper). Téléchargement par yt-dlp et ffmpeg.
- Mobile : PWA Vite (`mobile/`). Transcription dans le navigateur (Transformers.js, Whisper ONNX), historique IndexedDB.
- Flux YouTube mobile : téléphone, tunnel, pont Mac `dev_server.py` (yt-dlp, ffmpeg, mp3), retour au téléphone, Worker, historique.
- Flux fichier local : téléphone, Worker, historique (sans pont).
- Authentification actuelle : un jeton unique par lancement du pont, transmis par `#key=`, stocké dans `localStorage`.
- Transversal [C] : trois `is_youtube_url` aux règles différentes (GUI : http et https sans contrôle d'utilisateur ni de port ; pont : https seulement, sans utilisateur, port 443 ; JS : https). Le CLI n'en a pas.

## 1. mobile/index.html (95 lignes)
Rôle : coquille HTML unique ; charge `./src/main.js` ; les styles viennent de l'import CSS de `main.js`.
Éléments : lien YouTube, bloc caché `session-box`, erreur `role="alert"`, sélecteur de fichier `audio/*`, vitesse, langue, bouton Transcrire, progression `aria-live`, résultat, historique, aide d'installation.
- [C] l.34-37 : champ « Code temporaire de test », placeholder « reçu dans le chat » (cœur du P0).
- [C] l.26, 33, 85-86 : « iPhone » et « Mac de test » en dur.
- [C] l.91 : le premier téléchargement du modèle n'est expliqué que dans le pied de page, sans taille ni durée.
- [C] l.10 : `apple-touch-icon` en 192 px (iOS attend d'ordinaire 180 px, [H]). Pas de `<noscript>`.
- [C] l.25 et 26 : « en privé » alors que l'audio YouTube passe par le Mac (voir NOUV-30).
Tâches : NOUV-10, NOUV-27, NOUV-30.

## 2. mobile/src/main.js (374 lignes)
Rôle : câblage du DOM, jeton, source audio, dialogue avec le Worker, IndexedDB, export, installation, service worker.
Fonctionnement : jeton lu dans `localStorage` puis `#key=` (retiré de l'URL, l.30-38) ; `getAudioSource` (l.232-257) appelle `./api/youtube-audio` ou lit le fichier ; le clic Transcrire (l.259) envoie l'`ArrayBuffer` au Worker ; le résultat est enregistré (l.288-316).
- M1 [C] l.30-38, 193-199, 236 : code de session obligatoire ; bouton grisé sans jeton (P0, relève de MOB-S).
- M2 [C] l.243-247, 38, 198 : un 401 n'efface pas le jeton ; la saisie reste cachée dès qu'un jeton existe (P0).
- M3 [C] l.30-34 : `localStorage` sans `try/catch`. [H] une exception bloquerait tout le script.
- M4 [C] l.331-333 et 45-54 : après une erreur, la barre redevient indéterminée ; l'erreur n'est pas affichée dans `youtube-error`.
- M5 [C] l.238-242 : `fetch` sans délai maximal, sans annulation ; message réseau brut.
- M6 [C] l.252, 256 : audio lu entièrement en mémoire, sans limite côté mobile (le pont peut envoyer 250 Mo).
- M7 [C] l.151, 237, 274, 302, 305, 309 : « iPhone » et « Mac de test » en dur.
- M8 [C] l.3, 30 : base et jeton liés à l'origine. [H] avec un tunnel rapide, perte du jeton, de l'historique et du cache modèle à chaque nouvelle adresse.
- M9 [C] l.372-374 : erreur d'enregistrement du service worker avalée ; aucune détection de nouvelle version.
- M10 [C] l.272 : `await navigator.storage.persist()` avant tout le reste.
- M11 [H] l.158-171 : le repli en téléchargement après un `await` peut être refusé par Safari.
- M12 [C] l.43 : Worker créé sans `try/catch`.
- M13 [C] l.364-369 : aide d'installation seulement pour Safari iOS.
- M14 [C] l.37 : le jeton est recopié dans un champ texte (caché).
- Points corrects : DOM construit avec `textContent` ; fragment `#key=` retiré ; erreur d'enregistrement de l'historique bien traitée ; nom de fichier de sortie nettoyé.
Tâches : MOB-S, NOUV-01, 08, 10, 13, 14, 15, 16, 17, 18.

## 3. mobile/src/transcriber.worker.js (70 lignes)
Rôle : exécute Whisper hors du thread principal ; messages `status`, `progress`, `result`, `error`.
Fonctionnement : cache navigateur du modèle ; `Map` de pipelines par `modèle:moteur` ; `q8` ; WebGPU puis repli CPU à la création ; URL `blob:` passée au pipeline avec `chunk_length_s: 30`, `stride_length_s: 5`.
- W1 [H] l.58-62 : le décodage audio d'une URL `blob:` dans un Worker demande `AudioContext`, absent des Workers. Si confirmé, YouTube et fichier local échouent tous deux. À tester d'abord sur le Mac (NOUV-20). Correctif envisagé (NOUV-03) : décoder dans le thread principal, rééchantillonner en 16 kHz mono, passer un `Float32Array`.
- W2 [C] l.43-55 : le repli WebGPU vers WASM n'existe qu'à la création ; un plantage pendant la transcription part en erreur sans nouvel essai.
- W3 [C] l.7, 15 : pipelines jamais libérés.
- W4 [C] l.17-27 : pas de progression pendant la transcription.
- W5 [C] l.36 : pas d'identifiant de requête ni d'annulation ; deux messages tournent en parallèle.
- W6 [H] : cache modèle lié à l'origine (voir M8).
- W7 [H] : un long audio décodé en `Float32Array` 16 kHz dépasse la mémoire d'un téléphone (limite de durée à définir).
- W8 [H] l.29 : `q8` imposé aussi pour WebGPU, stabilité sur iOS inconnue.
Tâches : NOUV-03, 07, 08, 09, 11, 12, 20.

## 4. mobile/src/style.css (67 lignes)
Rôle : styles de toute l'interface, minifiés par lignes.
- [C] l.4 : `font: inherit` pour `button, select, textarea`, pas pour `input`. [H] zoom automatique de Safari iOS sur les champs de moins de 16 px.
- [C] aucun `prefers-reduced-motion`, aucun mode sombre.
- [C] polices de 11 et 12 px (aide, historique) ; cibles tactiles de 38 à 46 px (Apple recommande 44).
- [C] `progress` : seuls les pseudo-éléments de valeur sont stylés ; l'apparence indéterminée dépend du navigateur.
- Points corrects : `[hidden] { display: none !important }` ; champ fichier masqué de façon accessible ; `safe-area-inset`.
Tâches : NOUV-26.

## 5. mobile/public/sw.js (38 lignes)
Rôle : service worker ; précache de la coquille ; cache d'abord pour tout GET de même origine.
- [C] l.22-25 : tout GET de même origine est servi depuis le cache s'il y est, y compris `index.html` ; une nouvelle version n'apparaît que si `CACHE_NAME` (l.1, `v5`) change.
- [C] l.5 : `cache.addAll` est tout ou rien. [H] si un fichier de la liste est absent (une icône), l'installation échoue.
- [C] l.6, 13 : `skipWaiting` et `clients.claim` ; une nouvelle version prend la main sans prévenir.
- [C] l.28 : `cache.put` sans `event.waitUntil`.
- [H] avec un tunnel rapide mort, l'icône installée ouvre quand même la coquille depuis le cache ; seul l'appel `/api` échoue.
- Points corrects : POST et origines tierces (modèles) non interceptés ; anciens caches supprimés à l'activation.
Tâches : NOUV-04, 17, 27.

## 6. mobile/public/manifest.webmanifest (18 lignes)
- [C] `start_url` et `scope` en `./`, `display: standalone`, `orientation: portrait`.
- [C] icônes 192, 512 et SVG en `purpose: any` ; pas d'icône maskable.
- [C] aucun jeton dans `start_url`.
- [H] iOS utilise `apple-touch-icon`, pas le manifeste.
Tâches : NOUV-27.

## 7. mobile/vite.config.js (7 lignes) et mobile/package.json (17 lignes)
- [C] `base: './'` ; `server.host` et `preview.host` à `0.0.0.0` (expose le serveur au réseau local).
- [C] versions exactes : `@huggingface/transformers` 4.3.2, `vite` 8.3.6 ; version `0.1.0` ; `private`.
- [C] pas de champ `engines` (le README annonce Node 20.19 ou plus) ; pas de script de test ; pas de licence.
- [C] `npm run dev` n'a pas le pont `/api`.
Tâches : NOUV-25.

## 8. mobile/dev_server.py (175 lignes)
Rôle : sert `dist/` et expose `POST /api/youtube-audio` : contrôle du jeton, validation de l'URL, un téléchargement à la fois (`BoundedSemaphore`), yt-dlp puis mp3, réponse binaire.
Points corrects [C] : écoute sur `127.0.0.1` ; `hmac.compare_digest` ; corps limité à 16 Ko ; audio limité à 250 Mo ; dossier temporaire ; pas de journal des URL ; URL https YouTube sans utilisateur ni port ; titre nettoyé ; fermeture de connexion gérée.
- D1 [C] l.58-62 : `duration is None` passe le filtre ; un livestream n'est pas borné (P0).
- D2 [H] l.70 : `noplaylist` ne protège pas une URL `playlist?list=` (comportement documenté de yt-dlp, non testé ici) (P0).
- D3 [H] : une URL YouTube sans extracteur dédié tombe sur l'extracteur générique, qui peut suivre des redirections ; limiter avec `allowed_extractors` (P0).
- D4 [C] l.111 : `compare_digest` sur des `str` ; un en-tête non ASCII lève `TypeError`. Comparer en `bytes`.
- D5 [C] l.24 : aucune longueur minimale pour `QUICK_T_LINK_TOKEN`.
- D6 [C] l.164 : jeton affiché dans le terminal ; aucun mécanisme de remise à la PWA installée.
- D7 [C] l.140 : message yt-dlp brut (240 caractères) renvoyé au client ; pas de tri vidéo privée / indisponible / région.
- D8 [C] l.72 : `socket_timeout` ne couvre qu'une opération réseau ; aucun délai global ; aucune annulation si le client coupe.
- D9 [C] l.119-121 : `Content-Length` absent ou nul répond 413 « trop volumineuse ».
- D10 [H] l.136-152 : aucun octet n'est envoyé avant la fin de la conversion ; le tunnel peut couper une requête longue (environ 100 s, à vérifier).
- D11 [H] l.78-84 : si le filtre de durée rejette la vidéo, yt-dlp ne produit pas de fichier et l'utilisateur voit « fichier audio attendu » avant le vrai motif.
- D12 [C] classe `SimpleHTTPRequestHandler` : index de répertoire possible, pas de `Cache-Control` ni de CSP / Referrer-Policy sur le statique, pas de délai sur les sockets entrantes.
- D13 [H] l.19 : le port 4173 est, à ma connaissance, aussi celui de `vite preview`.
Tâches : BRG, NOUV-02, 05, 19, 21, 22.

## 9. mobile/test_bridge.py (110 lignes)
- [C] teste `is_youtube_url`, `safe_title`, l'appel de `download_youtube_audio` avec un faux yt-dlp, et trois erreurs API (401, 400, 400).
- [C] le jeton `test-session-token` (l.64) est factice.
- [C] pas de test du 413, du 429, du succès, des playlists ni des livestreams.
- [C] `test_download_options_limit_duration_and_playlists` ne vérifie que la durée, pas `noplaylist`.
- [C] `import dev_server` impose de lancer depuis `mobile/` et d'avoir `yt_dlp`.
Tâches : NOUV-31 (sur demande).

## 10. mobile/README.md (41 lignes)
- [C] décrit bien le flux (pont, tunnel, `/#key=CODE`).
- [C] l.30 : le repli WASM est annoncé de façon trop large (voir W2).
- [C] pas de mention de `QUICK_T_LINK_TOKEN`, des tests, ni de la durée de vie du code (un redémarrage du pont change le code).
- [C] licences : `whisper-tiny` sans licence déclarée (AU-05).
Tâches : GIT, NOUV-25.

## 11. Quick_T.py (102 lignes, CLI)
Rôle : télécharge une vidéo, transcrit avec openai-whisper, écrit un `.txt` dans `~/Documents/Transcriptions`.
Points corrects [C] : arguments, nom de fichier portable, nom unique, écriture par fichier `.part`, nettoyage des temporaires, sortie non nulle en cas d'échec.
- [C] l.12 : URL par défaut codée en dur.
- [C] pas de validation d'URL, pas de contrôle de ffmpeg, pas de limite de durée, de taille ni de playlist.
- [C] pas d'entrée par fichier audio local.
- [C] l.9 : `import whisper` ; sur PyPI le paquet s'appelle `openai-whisper`, `whisper` est un autre paquet (à documenter).
- [C] sortie : une ligne terminée par `\n`, alors que la GUI écrit sans retour à la ligne final.
Tâches : NOUV-23, 24, 25, 28, 29.

## 12. Quick_T_gui.py (448 lignes, Tkinter)
Rôle : plusieurs URL, téléchargements parallèles (1 à 6), transcription séquentielle avec faster-whisper (CPU, int8), arrêt, ouverture du fichier.
Points corrects [C] : file d'attente entre threads et interface ; contrôle d'URL, de ffmpeg et du dossier ; écriture par `.part` ; arrêt propre ; fermeture différée.
- G1 [C] l.26-37 : accepte `http` et `https`, sans contrôle d'utilisateur ni de port.
- G2 [H] l.339-347 : pas de limite de durée ni de taille ; une URL de playlist peut télécharger toute la liste dans le même fichier de base (le dernier élément resterait) ; un livestream n'est pas borné.
- G3 [C] l.414 : texte écrit sans retour à la ligne, avec une espace finale.
- G4 [C] l.419-423 : un texte partiel est renommé en fichier final sans marque.
- G5 [C] l.328 : audio temporaire dans le dossier de sortie. [H] si ce dossier est synchronisé (iCloud), les temporaires partent dans le nuage ; un arrêt brutal les laisse.
- G6 [C] l.388 : toujours CPU ; pas d'indication de téléchargement du modèle ; le mode accéléré dépend de la version de faster-whisper (à épingler).
- G7 [C] : pas d'entrée par fichier audio local ; titre de fenêtre non aligné sur « Quick T ».
Tâches : NOUV-23, 24, 25, 28.

## 13. test_quick_t.py (55 lignes)
- [C] tests de noms de fichiers, de réglages de vitesse et d'URL.
- [C] importe `Quick_T_gui` et `Quick_T` : exige `tkinter`, `yt_dlp`, `faster_whisper` et `whisper` installés.
- [C] ne teste ni `http` ni les faux domaines pour la GUI, ni le pipeline.
- [C] aucun lancement sur `shu_reference` à ce jour.
Tâches : NOUV-31 (sur demande).

## 14. .gitignore (32 lignes) et .env.example (4 lignes)
- [C] `.gitignore` couvre Python, Node, secrets, médias, modèles, journaux, sorties.
- [C] non couverts : `*.part`, `temp_*`, `.vscode/`, `.idea/`.
- [C] `.env.example` : variable vide, bien documentée ; [C] aucun code ne charge un `.env`, seulement `os.environ`.
Tâches : NOUV-25.

## 15. A/Quick_T.py (39 lignes) et A/Quick_T_gui.py (320 lignes)
- [C] versions plus anciennes, dépassées par la racine.
- [C] chemin absolu personnel codé en dur (`A/Quick_T.py` l.9, `A/Quick_T_gui.py` l.17), déjà dans l'historique public.
- [C] `A/Quick_T.py` : sortie sans création de dossier, temporaire à nom fixe, aucun traitement d'erreur, nettoyage seulement en cas de succès.
- [C] `A/Quick_T_gui.py` : pas de contrôle d'URL, de ffmpeg ni de dossier de sortie sûr ; fenêtre fermée sans attendre les threads ; fichier partiel laissé en cas d'échec ; langue par défaut `en`.
- Décision à prendre (GIT-03, NOUV-32) : supprimer `A/` par PR, l'historique gardant l'ancien contenu. Aucune réécriture d'historique sans accord.

## 16. Constats transversaux
- Le flux mobile n'a été vu fonctionner de bout en bout ni sur Mac ni sur appareil ; seule une partie du pont est couverte par des tests.
- Trois validations d'URL et deux moteurs desktop (openai-whisper, faster-whisper) : comportements différents.
- Aucun `requirements.txt` (GIT-07).
- Priorité de vérification : NOUV-20 (essai sur le navigateur du Mac) avant tout correctif du Worker.
