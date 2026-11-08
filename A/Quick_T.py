import yt_dlp
import whisper
import os

# -------- CONFIG --------
url = "https://www.youtube.com/watch?v=v7KXKht8Gjo"  # Mets ici ton URL YouTube
model_name = "base"                    # "small", "medium", "large"
language = "en"                        # langue de la vidéo
output_folder = "/Users/valentindardenne/Cours Data et project stage /Transcription"
# ------------------------

temp_audio = os.path.join(output_folder, "temp_audio.mp3")

ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': temp_audio.replace('.mp3', '.%(ext)s'),
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
    }],
    'quiet': True,
}

print("⏳ Téléchargement de l'audio...")
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(url, download=True)
    video_title = info.get('title', 'transcription')

print("🧠 Transcription en cours...")
model = whisper.load_model(model_name)
result = model.transcribe(temp_audio, language=language)

safe_title = video_title.replace(" ", "_").replace("/", "_")
output_path = os.path.join(output_folder, f"{safe_title}.txt")

with open(output_path, "w", encoding="utf-8") as f:
    f.write(result["text"])

os.remove(temp_audio)
print(f"✅ Transcription terminée ! Fichier créé : {output_path}")