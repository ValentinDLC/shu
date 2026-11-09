"""Local development bridge: serves the PWA and fetches YouTube audio for it."""
import hmac
import json
import os
import re
import secrets
import shutil
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, urlsplit

import yt_dlp

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
HOST = "127.0.0.1"
PORT = 4173
MAX_BODY_BYTES = 16 * 1024
MAX_AUDIO_BYTES = 250 * 1024 * 1024
MAX_DURATION_SECONDS = 3 * 60 * 60
DOWNLOAD_LOCK = threading.BoundedSemaphore(1)
ACCESS_TOKEN = os.environ.get("QUICK_T_LINK_TOKEN") or secrets.token_urlsafe(24)


def is_youtube_url(value: str) -> bool:
    try:
        parsed = urlsplit(value.strip())
        host = (parsed.hostname or "").lower().rstrip(".")
        return (
            parsed.scheme == "https"
            and parsed.username is None
            and parsed.password is None
            and parsed.port in (None, 443)
            and (
                host == "youtu.be"
                or host.endswith(".youtu.be")
                or host == "youtube.com"
                or host.endswith(".youtube.com")
            )
        )
    except ValueError:
        return False


def safe_title(value: str) -> str:
    value = re.sub(r'[\\/*?:"<>|\x00-\x1f]', "_", value).strip().rstrip(". ")
    value = re.sub(r"\s+", " ", value)[:160]
    return value or "youtube_audio"


def download_youtube_audio(url: str, folder: Path):
    """Return (mp3_path, title), raising a concise exception on failure."""
    token = secrets.token_hex(12)
    output_base = folder / token

    def duration_filter(info, *, incomplete):
        duration = info.get("duration")
        if duration is not None and duration > MAX_DURATION_SECONDS:
            return "La vidéo dépasse la durée maximale de 3 heures pour cet essai."
        return None

    options = {
        "format": "bestaudio/best",
        "outtmpl": str(output_base) + ".%(ext)s",
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "max_filesize": MAX_AUDIO_BYTES,
        "socket_timeout": 20,
        "retries": 2,
        "match_filter": duration_filter,
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
    audio_path = Path(str(output_base) + ".mp3")
    if not audio_path.is_file():
        raise RuntimeError("YouTube n’a pas fourni le fichier audio attendu.")
    if audio_path.stat().st_size > MAX_AUDIO_BYTES:
        audio_path.unlink(missing_ok=True)
        raise RuntimeError("Le fichier audio dépasse la limite de 250 Mo pour cet essai.")
    return audio_path, safe_title(info.get("title") or "youtube_audio")


class BridgeHandler(SimpleHTTPRequestHandler):
    server_version = "QuickTMobile/0.1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST), **kwargs)

    def log_message(self, _format, *args):
        # Évite d’enregistrer les URL des vidéos dans les journaux du serveur.
        return

    def _json(self, status: int, message: str):
        payload = json.dumps({"error": message}, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        if self.path != "/api/youtube-audio":
            self._json(404, "Adresse introuvable.")
            return
        supplied = self.headers.get("Authorization", "")
        if not hmac.compare_digest(supplied, f"Bearer {ACCESS_TOKEN}"):
            self._json(401, "Session de test non autorisée. Ouvre le lien Quick T complet.")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._json(400, "Requête invalide.")
            return
        if length <= 0 or length > MAX_BODY_BYTES:
            self._json(413, "Requête trop volumineuse.")
            return
        try:
            body = json.loads(self.rfile.read(length))
            url = body.get("url", "")
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            self._json(400, "Le lien reçu est invalide.")
            return
        if not isinstance(url, str) or not is_youtube_url(url):
            self._json(400, "Colle un lien YouTube HTTPS valide (youtube.com ou youtu.be).")
            return
        if not DOWNLOAD_LOCK.acquire(blocking=False):
            self._json(429, "Un autre téléchargement est déjà en cours. Réessaie dans un instant.")
            return

        try:
            with tempfile.TemporaryDirectory(prefix="quickt-mobile-") as temp_dir:
                try:
                    audio_path, title = download_youtube_audio(url, Path(temp_dir))
                except Exception as exc:
                    self._json(422, f"Impossible de récupérer cette vidéo : {str(exc)[:240]}")
                    return
                size = audio_path.stat().st_size
                self.send_response(200)
                self.send_header("Content-Type", "audio/mpeg")
                self.send_header("Content-Length", str(size))
                self.send_header("Content-Disposition", f"attachment; filename=audio.mp3; filename*=UTF-8''{quote(title)}.mp3")
                self.send_header("X-Source-Title", quote(title))
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                with audio_path.open("rb") as audio:
                    shutil.copyfileobj(audio, self.wfile, length=1024 * 1024)
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            DOWNLOAD_LOCK.release()


def main():
    if not DIST.is_dir() or not (DIST / "index.html").is_file():
        raise SystemExit("Compile d’abord l’application avec npm run build.")
    server = ThreadingHTTPServer((HOST, PORT), BridgeHandler)
    print(f"Quick T mobile en local : http://{HOST}:{PORT}")
    print(f"Code temporaire de la session : {ACCESS_TOKEN}")
    print("Ctrl+C arrête le serveur et le pont YouTube.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
