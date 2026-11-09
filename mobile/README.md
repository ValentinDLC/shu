# Quick T Mobile — prototype PWA

Cette application web progressive est le premier client mobile du projet. Elle fonctionne dans un navigateur récent, installe une icône sur l’écran d’accueil et transcrit localement un fichier audio avec Transformers.js et Whisper ONNX. Le moteur desktop Faster-Whisper reste séparé.

## Démarrage

Prérequis : Node.js 20.19 ou supérieur, npm, Python avec `yt-dlp` et FFmpeg. `yt-dlp` ne sert qu’au pont local qui récupère l’audio YouTube.

```sh
npm install
npm run build
python3 dev_server.py
```

Le serveur local affiche un code de session temporaire. Pour un essai sur iPhone, démarre le tunnel Cloudflare vers `http://127.0.0.1:4173` puis ouvre l’adresse du tunnel suivie de `/#key=CODE_TEMPORAIRE`. Le code est gardé dans le stockage local de Quick T et retiré de la barre d’adresse après lecture. Ne partage pas le lien complet de session. Le pont n’accepte que des URL HTTPS YouTube, une demande à la fois et des vidéos de trois heures maximum.

Pour produire les fichiers statiques :

```sh
npm run build
npm run preview
```

Le dossier `dist/` doit être hébergé en HTTPS pour permettre l’installation PWA et l’usage du service worker. Sur iPhone/iPad, ouvrir le site dans Safari puis « Partager » → « Sur l’écran d’accueil ». Sur Android, utiliser « Installer l’application » quand le navigateur le propose.

## Profils du téléphone

- **Rapide** : `onnx-community/whisper-tiny`, quantification Q8.
- **Équilibré** : `onnx-community/whisper-base`, quantification Q8.
- WebGPU est tenté quand le navigateur le propose ; en cas d’échec, le client retente sur le moteur WASM.
- Les poids et le runtime WASM sont conservés dans le cache navigateur par Transformers.js. Le premier téléchargement exige Internet et peut être volumineux. Le navigateur peut nettoyer son stockage ; le fonctionnement hors ligne après téléchargement doit donc être vérifié sur chaque appareil ciblé.

## Limites actuelles

Cette base traite soit un lien YouTube (le Mac local récupère l’audio via le pont de test, puis l’iPhone effectue la transcription), soit un fichier audio importé (transcription directe sur l’iPhone). Les transcriptions sont enregistrées dans un historique local IndexedDB sur l’appareil ; l’export ouvre la feuille de partage iOS si elle est disponible, pour choisir « Enregistrer dans Fichiers ». L’extraction de la piste audio depuis une vidéo locale et l’import via la feuille de partage iOS/Android ne sont pas encore implémentés. Il faut garder la page ouverte pendant l’inférence. iOS Safari et Android doivent être testés sur appareils physiques avant toute promesse de compatibilité ou de vitesse.

Pour un lien YouTube, le Mac de test récupère l’audio et le transmet à l’iPhone par le tunnel HTTPS ; la transcription par modèle se fait ensuite sur l’iPhone. Pour un fichier importé, le fichier reste sur l’iPhone. Le navigateur télécharge le code statique et les fichiers du modèle depuis leurs dépôts lors du premier usage. Aucun endpoint d’inférence n’est utilisé.

## Licences

Le code de l’application et ses dépendances doivent être vérifiés lors de la préparation commerciale. La fiche du modèle `onnx-community/whisper-base` indique Apache-2.0. La fiche `onnx-community/whisper-tiny` ne déclare pas de licence visible dans ses métadonnées au moment de cet audit ; ne pas le distribuer commercialement avant clarification de ses droits.
