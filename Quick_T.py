import argparse
import os
import re
import sys
import uuid
from pathlib import Path

import yt_dlp
import whisper

# -------- CONFIGURATION PAR DÉFAUT --------
DEFAULT_URL = "https://www.youtube.com/watch?v=v7KXKht8Gjo"
DEFAULT_MODEL = "base"
DEFAULT_LANGUAGE = "auto"
DEFAULT_OUTPUT = Path.home() / "Documents" / "Transcriptions"
MODELS = ("tiny", "base", "small", "medium", "large", "large-v2", "large-v3")
SPEED_BEAM_SIZES = {"rapide": 1, "equilibre": 3, "precis": 5}
# -------------------------------------------


def safe_filename(title: str) -> str:
    """Produit un nom compatible avec Windows, macOS et Linux."""
    name = re.sub(r'[\\/*?:"<>|\x00-\x1f]', "_", title).strip().rstrip(". ")
    name = re.sub(r"\s+", "_", name)[:150] or "transcription"
    if name.upper().split(".")[0] in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}:
        name = f"_{name}"
    return name


def unique_output_path(folder: Path, title: str) -> Path:
    base = safe_filename(title)
    path = folder / f"{base}.txt"
    suffix = 2
    while path.exists():
        path = folder / f"{base}_{suffix}.txt"
        suffix += 1
    return path


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Télécharge et transcrit une vidéo YouTube.")
    parser.add_argument("--url", default=DEFAULT_URL, help="URL YouTube à transcrire")
    parser.add_argument("--model", choices=MODELS, default=DEFAULT_MODEL, help="Modèle Whisper à utiliser")
    parser.add_argument("--language", default=DEFAULT_LANGUAGE, help="Langue (auto, fr, en, es…)")
    parser.add_argument("--speed", choices=tuple(SPEED_BEAM_SIZES), default="rapide",
                        help="rapide privilégie la vitesse, précis privilégie la qualité")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Dossier de destination")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    output_folder = args.output.expanduser()
    temp_audio = output_folder / f"temp_{uuid.uuid4().hex}.mp3"
    output_folder.mkdir(parents=True, exist_ok=True)
    try:
        print("⏳ Téléchargement de l'audio…")
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(temp_audio.with_suffix("")) + ".%(ext)s",
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
            "quiet": True,
            "noplaylist": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(args.url, download=True)
        if not temp_audio.is_file():
            raise FileNotFoundError("Le fichier audio attendu est introuvable après le téléchargement.")

        print(f"🧠 Transcription en cours avec le modèle {args.model} ({args.speed})…")
        model = whisper.load_model(args.model)
        language = None if args.language.lower() == "auto" else args.language
        result = model.transcribe(
            str(temp_audio), language=language,
            beam_size=SPEED_BEAM_SIZES[args.speed])

        output_path = unique_output_path(output_folder, info.get("title") or "transcription")
        partial_path = output_path.with_suffix(".txt.part")
        try:
            partial_path.write_text(result["text"].strip() + "\n", encoding="utf-8")
            os.replace(partial_path, output_path)
        finally:
            try:
                partial_path.unlink()
            except FileNotFoundError:
                pass
        print(f"✅ Transcription terminée ! Fichier créé : {output_path}")
        return 0
    except Exception as e:
        print(f"❌ Échec : {e}", file=sys.stderr)
        return 1
    finally:
        # Nettoie l'audio ou les fichiers intermédiaires laissés par yt-dlp.
        for candidate in output_folder.glob(temp_audio.stem + "*"):
            try:
                candidate.unlink()
            except OSError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
