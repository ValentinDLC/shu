# Quick T — Cahier des tâches (application complète)

**Propriétaire :** Valentin Dardenne
**Créé le :** 2026-11-09
**Source :** CAHIER_DES_CHARGES_QUICK_T.md + module Git/GitHub/sauvegardes
**Statut du document :** proposition, à valider par Valentin

## 0. Lecture du document

- Priorités : P0 bloquant, P1 important, P2 utile, P3 plus tard.
- États : ☐ à faire, ◐ annoncé dans le cahier des charges mais non vérifié dans le code, ✔ fait et vérifié.
- Ce document découle du cahier des charges et non d'une lecture du code. La tâche AU-01 sert à confronter les deux.
- Toute tâche qui engage de l'argent, une publication ou un envoi à des tiers exige l'accord explicite de Valentin.
- Les tâches de tests sont des propositions à valider, aucun test n'étant lancé sans demande.

## 1. Dépôt, sauvegardes, documentation (GIT)

| ID | P | État | Tâche | Critère de fin |
|---|---|---|---|---|
| GIT-01 | P0 | ☐ | Importer le travail de A dans ValentinDLC/shu via la branche chore/import-quick-t, puis une Pull Request | Fichiers visibles sur GitHub, push confirmé, aucun secret |
| GIT-02 | P0 | ☐ | Créer .gitignore et .env.example (sans vraie clé) | Aucun venv, cache, média, modèle ni secret suivi |
| GIT-03 | P0 | ☐ | Trancher la structure : ancien dossier A/ du dépôt contre racine | Décision écrite ; A/ supprimé seulement après diff validé |
| GIT-04 | P1 | ☐ | Créer develop ; activer la protection de main (PR obligatoire, pas de push forcé) | Réglages GitHub confirmés par Valentin |
| GIT-05 | P1 | ☐ | Dépôt Git parent « workspace » sans commit : décider de son sort, sans rien supprimer sans accord | Plus de risque d'ajout accidentel |
| GIT-06 | P1 | ☐ | Rédiger README.md, CHANGELOG.md, CONTRIBUTING.md, docs/ARCHITECTURE.md | Documentation conforme au code réel |
| GIT-07 | P1 | ☐ | Lister les dépendances (requirements, package.json) avec versions | Installation reproductible depuis zéro |
| GIT-08 | P2 | ☐ | Contrôle anti-secrets avant chaque push (manuel ou hook) | Procédure documentée |
| GIT-09 | P2 | ☐ | Décider si le dépôt « shu » est renommé en Quick T | Décision de Valentin |
| GIT-10 | P2 | ☐ | Identifier le « second dossier » cité par le module Git | Dossier comparé, doublons non supprimés avant analyse |
| GIT-11 | P1 | ☐ | Tag v0.1 avec notes (changements, fonctions, problèmes connus, lancement, tests) | Tag poussé et confirmé |

## 2. Audit initial (AU)

| ID | P | État | Tâche | Critère de fin |
|---|---|---|---|---|
| AU-01 | P0 | ☐ | Comparer code et cahier des charges, avec preuves (fichier, fonction) | Liste d'écarts classée |
| AU-02 | P0 | ☐ | Relire dev_server.py : domaines autorisés, redirections, limites, authentification, nettoyage | Rapport de risques |
| AU-03 | P1 | ☐ | Relire test_quick_t.py et mobile/test_bridge.py | État et couverture connus |
| AU-04 | P1 | ☐ | Rejouer npm run build et les tests Python du pont | Résultats consignés sans extrapolation |
| AU-05 | P1 | ☐ | Vérifier les licences des dépendances et des modèles (Whisper Tiny ONNX signalé incertain) | Tableau des licences |

## 3. Mobile : session et pont YouTube (MOB-S) — priorité absolue

| ID | P | État | Tâche | Critère de fin |
|---|---|---|---|---|
| MOB-S1 | P0 | ☐ | Diagnostiquer « Session de test manquante » (Safari, PWA installée, onglet privé, stockage distinct iOS, URL d'entrée) | Cause prouvée |
| MOB-S2 | P0 | ☐ | Concevoir une session sans code manuel et comparer les options (lien/QR à usage unique échangé contre un jeton révocable, ré-appairage, etc.) | Arbitrage écrit, option choisie |
| MOB-S3 | P0 | ☐ | Implémenter la session choisie, jeton temporaire et jamais dans le dépôt | Parcours sans saisie de code |
| MOB-S4 | P0 | ☐ | Gérer expiration, Mac redémarré, tunnel perdu, serveur arrêté, hors ligne | Message clair et action de reconnexion pour chaque cas |
| MOB-S5 | P0 | ☐ | Script de démarrage/arrêt du pont sur Mac, tunnel identifié comme temporaire | Procédure en 2 commandes maximum |
| MOB-S6 | P0 | ☐ | Essai YouTube réel sur iPhone, étape par étape | Compte rendu daté, avec temps et erreurs |

## 4. Pont YouTube : sécurité et robustesse (BRG)

| ID | P | État | Tâche | Critère de fin |
|---|---|---|---|---|
| BRG-01 | P0 | ☐ | Accepter seulement les URL YouTube attendues (youtube.com, youtu.be), refuser les redirections arbitraires | Pas de proxy ouvert |
| BRG-02 | P0 | ☐ | Limiter taille, durée et concurrence ; authentifier tous les points d'API | Limites documentées |
| BRG-03 | P1 | ☐ | Erreurs yt-dlp : vidéo privée, indisponible, région, sans audio | Messages utilisateur distincts |
| BRG-04 | P1 | ☐ | Supprimer les audios temporaires, même en cas d'échec | Dossier temporaire vide après erreur |
| BRG-05 | P1 | ☐ | Journaux sans jetons ni URL privées | Revue des logs |
| BRG-06 | P2 | ☐ | Étendre test_bridge.py aux cas ci-dessus (sur validation de Valentin) | Tests passants |
| BRG-07 | P3 | ☐ | Décider du sort du pont : temporaire, option avancée ou service hébergé | Décision écrite |

## 5. Mobile : transcription et performances (MOB-T)

| ID | P | État | Tâche | Critère de fin |
|---|---|---|---|---|
| MOB-T1 | P0 | ☐ | Valider l'import de fichier audio sans pont, sur iPhone | Essai réel consigné |
| MOB-T2 | P1 | ☐ | Lister les formats réellement décodables et refuser proprement les autres | Message explicite |
| MOB-T3 | P1 | ☐ | Afficher les étapes : récupération, chargement du modèle, transcription, sauvegarde | Statut toujours visible |
| MOB-T4 | P1 | ☐ | Annulation et nettoyage | Retour à un état propre |
| MOB-T5 | P1 | ☐ | Profils Rapide / Équilibré / Qualité sans jargon, choix automatique du moteur | Profils compréhensibles |
| MOB-T6 | P1 | ☐ | Repli WebGPU vers WASM fiable | Pas de plantage sans WebGPU |
| MOB-T7 | P1 | ☐ | Protocole de mesures : appareil, navigateur, durée audio, temps modèle, temps inférence, mémoire, chauffe | Tableau de résultats reproductible |
| MOB-T8 | P1 | ☐ | Limites de durée/mémoire et découpage en segments si utile | Erreur utile à la place d'un crash |
| MOB-T9 | P1 | ☐ | Expliquer le premier téléchargement du modèle (taille mesurée, stockage, connexion) | Texte sans promesse non mesurée |
| MOB-T10 | P2 | ☐ | Comparer Tiny et Base, quantification, précision contre vitesse | Arbitrage documenté |
| MOB-T11 | P2 | ☐ | Test hors ligne après cache | Résultat consigné |

## 6. Mobile : historique et export (MOB-H)

| ID | P | État | Tâche | Critère de fin |
|---|---|---|---|---|
| MOB-H1 | P0 | ☐ | Historique : titre/source, date, état, texte ; ouvrir, copier, exporter/partager, supprimer | Chaque action testée |
| MOB-H2 | P0 | ☐ | Indiquer que l'historique est local à l'appareil (pas de cloud) | Message visible |
| MOB-H3 | P0 | ☐ | Confirmation « terminé et enregistré » même après retour à l'accueil | Vérifié sur iPhone |
| MOB-H4 | P1 | ☐ | Persistance après redémarrage et mise à jour de la PWA | Aucune transcription perdue |
| MOB-H5 | P1 | ☐ | Conserver accents, paragraphes, segments utiles | Texte lisible à l'export |
| MOB-H6 | P3 | ☐ | Formats d'export supplémentaires (SRT...) | À décider |

## 7. PWA : installation et cache (PWA)

| ID | P | État | Tâche | Critère de fin |
|---|---|---|---|---|
| PWA-01 | P1 | ☐ | Vérifier manifest, icônes, nom, mode autonome | Installation correcte |
| PWA-02 | P1 | ☐ | Stratégie de cache et versionnement du service worker, sans ancien JS servi | Mise à jour testée |
| PWA-03 | P1 | ☐ | Installer et lancer depuis l'écran d'accueil : iOS Safari, puis Android Chrome | Essais réels consignés |
| PWA-04 | P2 | ☐ | Documenter les quotas de stockage par navigateur | Section dédiée |

## 8. Bureau : GUI et CLI (DSK)

| ID | P | État | Tâche | Critère de fin |
|---|---|---|---|---|
| DSK-01 | P1 | ☐ | Rejouer : URL unique, plusieurs, doublons, vidéo indisponible, erreur réseau, annulation, nom dupliqué | Résultats consignés |
| DSK-02 | P1 | ☐ | Arrêt des téléchargements et fermeture pendant le travail ; nettoyage des temporaires | Aucun résidu |
| DSK-03 | P1 | ☐ | Ne jamais écraser une transcription existante ; chemin de sortie visible et modifiable | Vérifié |
| DSK-04 | P1 | ☐ | Erreurs claires si FFmpeg, yt-dlp ou le moteur sont absents | Messages actionnables |
| DSK-05 | P2 | ☐ | Harmoniser ou documenter les différences GUI (Faster-Whisper) et CLI (OpenAI Whisper) | Tableau comparatif |
| DSK-06 | P2 | ☐ | Comparer qualité et vitesse des profils sur un corpus autorisé | Matériel et résultats notés |
| DSK-07 | P2 | ☐ | Documenter l'installation macOS ; décider du support Windows/Linux | Procédure testée |
| DSK-08 | P3 | ☐ | Packaging/installateur après stabilisation | Décision puis livraison |

## 9. Accessibilité et qualité (QLT)

| ID | P | État | Tâche | Critère de fin |
|---|---|---|---|---|
| QLT-01 | P1 | ☐ | Matrice d'appareils réels : au moins 1 iPhone, 1 Android, gammes différentes | Liste fournie par Valentin |
| QLT-02 | P1 | ☐ | Journal de tests unique (date, appareil, résultat) | Fichier tenu à jour |
| QLT-03 | P2 | ☐ | Accessibilité : zones tactiles, libellés, contraste, VoiceOver/TalkBack, paysage | Contrôle effectué |

## 10. Légal, hébergement, distribution (DST)

| ID | P | État | Tâche | Critère de fin |
|---|---|---|---|---|
| DST-01 | P1 | ☐ | Rappel d'usage des droits YouTube dans l'application ; analyse des conditions avant distribution | Texte validé, sans promesse de conformité |
| DST-02 | P1 | ☐ | Politique de confidentialité (traitement local, exceptions du pont) | Texte vérifié contre le code |
| DST-03 | P2 | ☐ | Choisir un hébergement HTTPS permanent ; coût soumis à l'accord de Valentin | Décision écrite |
| DST-04 | P2 | ☐ | Architecture de service durable si le pont devient public | Revue sécurité |
| DST-05 | P2 | ☐ | Procédures d'installation, mise à jour, désinstallation, suppression des données | Documentation |
| DST-06 | P3 | ☐ | Support et canal de retours | Défini |

## 11. Jalons de version

| Version | Contenu minimal | Conditions |
|---|---|---|
| v0.1 | GIT-01 à GIT-03, AU-01 à AU-04, README ; bureau et import fichier mobile décrits tels qu'ils sont | Import mergé, tag poussé |
| v0.2 | MOB-S1 à S6, BRG-01 à BRG-04, MOB-T1 | YouTube de bout en bout sur iPhone réel |
| v0.5 | MOB-T, MOB-H, PWA-01 à 03, DSK-01 à 04, QLT-01 et 02 | Essais réels iOS et Android consignés |
| v1.0 | DST-01 à 05, AU-05, sécurité et confidentialité vérifiées | Hébergement durable et licences validées |

Les numéros sont indicatifs et suivront l'état réel du logiciel.

## 12. Décisions en attente de Valentin

1. Import par Pull Request ou directement sur main.
2. Structure du dépôt : racine ou dossier A/.
3. Nom du dépôt : shu ou Quick T.
4. Identification du second dossier.
5. Sort du dépôt Git parent « workspace ».
6. Appareils disponibles pour les essais réels.
7. Hébergement et budget éventuel.

## 13. Journal

| Date | Mise à jour |
|---|---|
| 2026-11-09 | Création du cahier des tâches. Aucune tâche réalisée. |


## Tâches ajoutées suite à l'audit (2026-11-09, numérotation provisoire NOUV-xx, à valider)

| Code | Priorité | Tâche |
|---|---|---|
| NOUV-01 | P0 | Mobile : effacer le jeton périmé sur 401, réafficher une saisie ou un message actionnable |
| NOUV-02 | P0 | Pont : refuser livestreams, playlists et extracteurs génériques ; ajouter un timeout global |
| NOUV-03 | P0 | Mobile : vérifier l'import audio local ; si `AudioContext` manque dans le Worker, décoder dans le thread principal (hypothèse à tester) |
| NOUV-04 | P1 | Service worker : réseau d'abord pour `index.html` et les navigations, pour ne pas servir un ancien JS |
| NOUV-05 | P1 | Pont : comparer le jeton en bytes, imposer une longueur minimale, trier les erreurs yt-dlp sans exposer de chemins |
| NOUV-06 | P2 | Historique : supprimer, copier, enregistrer les échecs ; remplacer « sur cet iPhone » en dur par un texte adapté à l'appareil |


## Tâches NOUV-07 à NOUV-32 (2026-11-09, issues de l'analyse par fichier, à valider)

| Code | Priorité | Tâche |
|---|---|---|
| NOUV-07 | P1 | Worker : si la transcription WebGPU échoue, relancer en WASM avant d'afficher une erreur (W2) |
| NOUV-08 | P1 | Mobile : limite de durée et de mémoire pour l'audio, message actionnable (W7, M6) |
| NOUV-09 | P1 | Worker : libérer le pipeline précédent au changement de modèle (W3) |
| NOUV-10 | P1 | Textes : retirer « iPhone », « Mac de test » et « reçu dans le chat » de l'interface (M7, index.html) |
| NOUV-11 | P2 | Progression pendant la transcription et taille du modèle annoncée avant le téléchargement (W4) |
| NOUV-12 | P2 | Worker : identifiant de requête, file d'attente et annulation (W5) |
| NOUV-13 | P1 | Après une erreur : arrêter la barre animée et afficher l'erreur dans une zone visible avec une action (M4) |
| NOUV-14 | P1 | `localStorage` dans un `try/catch`, avec repli en mémoire (M3) |
| NOUV-15 | P1 | `fetch` avec délai maximal, bouton Annuler et messages réseau actionnables (M5) |
| NOUV-16 | P2 | `storage.persist()` non bloquant, Worker protégé par `try/catch` (M10, M12) |
| NOUV-17 | P2 | Service worker : signaler une nouvelle version, journaliser l'échec d'enregistrement (M9) |
| NOUV-18 | P3 | Aide d'installation adaptée à Android et aux navigateurs iOS autres que Safari (M13) |
| NOUV-19 | P1 | Pont : tâche asynchrone (création, statut, récupération) pour éviter le délai du tunnel, afficher la progression et permettre l'annulation (D8, D10, hypothèse à tester) |
| NOUV-20 | P0 | Essai sur le navigateur du Mac (fichier audio local puis YouTube) pour valider Worker et décodage ; consigner le résultat réel (W1) |
| NOUV-21 | P1 | Pont : message distinct quand le filtre de durée rejette la vidéo ; réponse correcte si `Content-Length` est absent (D9, D11) |
| NOUV-22 | P2 | Pont : en-têtes de sécurité, `Cache-Control` du statique, pas d'index de répertoire, délai sur les sockets (D12) |
| NOUV-23 | P1 | GUI et CLI : mêmes bornes que le pont pour playlists, livestreams, durée et taille (G2) |
| NOUV-24 | P2 | Refactor : module commun pour la validation d'URL, les noms de fichiers et les options yt-dlp |
| NOUV-25 | P2 | Configuration : champ `engines` Node, `.env.example` expliqué (non chargé automatiquement), `requirements.txt` avec `openai-whisper` (voir GIT-07), versions épinglées |
| NOUV-26 | P2 | Interface : champs à 16 px minimum, `prefers-reduced-motion`, cibles tactiles de 44 px (CSS) |
| NOUV-27 | P2 | PWA : contrôler les icônes (`icon.svg`, 180 px, maskable), précache tout ou rien, app installée sur une ancienne adresse |
| NOUV-28 | P2 | Bureau : sortie cohérente CLI et GUI (retours à la ligne), texte partiel signalé, fichiers temporaires hors dossier de sortie (G3 à G5) |
| NOUV-29 | P2 | CLI : contrôle de ffmpeg, option fichier audio local, validation d'URL, pas d'URL par défaut |
| NOUV-30 | P2 | Confidentialité : reformuler « en privé » (l'audio YouTube passe par le Mac) et vérifier les requêtes réseau réelles de l'app |
| NOUV-31 | P3 | Tests : réécriture indépendante des dépendances lourdes, uniquement sur demande explicite de Valentin |
| NOUV-32 | P2 | GIT-03 : décider du sort de `A/` (contient un chemin personnel, déjà dans l'historique public) |
