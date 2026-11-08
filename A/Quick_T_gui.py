import os
import re
import sys
import uuid
import queue
import glob
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor

import yt_dlp
from faster_whisper import WhisperModel

# -------- VALEURS PAR DÉFAUT --------
DEFAULT_OUTPUT = "/Users/valentindardenne/Cours Data et project stage /Transcription"
MODELS = ["tiny", "base", "small", "medium", "large-v3"]
LANGUAGES = ["auto", "en", "fr", "es", "de", "it", "pt"]
# ------------------------------------


def unique_path(folder, title):
    safe = re.sub(r'[\\/*?:"<>|]', "_", title).strip().replace(" ", "_")[:150]
    safe = safe or "transcription"
    path = os.path.join(folder, f"{safe}.txt")
    n = 2
    while os.path.exists(path):
        path = os.path.join(folder, f"{safe}_{n}.txt")
        n += 1
    return path


class App:
    def __init__(self, root):
        self.root = root
        root.title("Transcripteur YouTube → Texte")
        root.geometry("820x700")

        self.ui_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.total = 0
        self.done = 0
        self.running = False

        self.build_ui()
        self.root.after(100, self.poll_ui_queue)
        root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------- Interface ----------
    def build_ui(self):
        pad = {"padx": 10, "pady": 4}

        ttk.Label(self.root, text="URLs YouTube (une par ligne) :").pack(anchor="w", **pad)
        self.url_text = tk.Text(self.root, height=6, wrap="none")
        self.url_text.pack(fill="x", **pad)

        opts = ttk.Frame(self.root)
        opts.pack(fill="x", **pad)

        ttk.Label(opts, text="Modèle :").grid(row=0, column=0, sticky="w")
        self.model_var = tk.StringVar(value="base")
        ttk.Combobox(opts, textvariable=self.model_var, values=MODELS,
                     width=10, state="readonly").grid(row=0, column=1, padx=(4, 16))

        ttk.Label(opts, text="Langue :").grid(row=0, column=2, sticky="w")
        self.lang_var = tk.StringVar(value="en")
        ttk.Combobox(opts, textvariable=self.lang_var, values=LANGUAGES,
                     width=6, state="readonly").grid(row=0, column=3, padx=(4, 16))

        ttk.Label(opts, text="Téléchargements simultanés :").grid(row=0, column=4, sticky="w")
        self.workers_var = tk.IntVar(value=3)
        ttk.Spinbox(opts, from_=1, to=6, textvariable=self.workers_var,
                    width=4).grid(row=0, column=5, padx=4)

        folder_row = ttk.Frame(self.root)
        folder_row.pack(fill="x", **pad)
        ttk.Label(folder_row, text="Dossier de sortie :").pack(side="left")
        self.folder_var = tk.StringVar(value=DEFAULT_OUTPUT)
        ttk.Entry(folder_row, textvariable=self.folder_var).pack(
            side="left", fill="x", expand=True, padx=6)
        ttk.Button(folder_row, text="Parcourir…", command=self.choose_folder).pack(side="left")

        btns = ttk.Frame(self.root)
        btns.pack(fill="x", **pad)
        self.start_btn = ttk.Button(btns, text="▶ Démarrer", command=self.start)
        self.start_btn.pack(side="left")
        self.stop_btn = ttk.Button(btns, text="■ Arrêter", command=self.stop, state="disabled")
        self.stop_btn.pack(side="left", padx=6)
        ttk.Button(btns, text="Ouvrir le dossier", command=self.open_folder).pack(side="left")

        self.tree = ttk.Treeview(self.root, columns=("titre", "statut"),
                                 show="headings", height=8)
        self.tree.heading("titre", text="Vidéo")
        self.tree.heading("statut", text="Statut")
        self.tree.column("titre", width=470)
        self.tree.column("statut", width=280)
        self.tree.pack(fill="both", expand=True, **pad)

        self.progress = ttk.Progressbar(self.root, mode="determinate")
        self.progress.pack(fill="x", **pad)

        ttk.Label(self.root, text="Journal :").pack(anchor="w", padx=10)
        self.log_text = tk.Text(self.root, height=8, state="disabled")
        self.log_text.pack(fill="both", expand=True, **pad)

    def choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_var.get() or "/")
        if folder:
            self.folder_var.set(folder)

    def open_folder(self):
        folder = self.folder_var.get().strip()
        if not os.path.isdir(folder):
            messagebox.showinfo("Dossier introuvable", "Le dossier n'existe pas encore.")
            return
        if sys.platform == "darwin":
            subprocess.Popen(["open", folder])
        elif sys.platform.startswith("win"):
            os.startfile(folder)
        else:
            subprocess.Popen(["xdg-open", folder])

    def log(self, text):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    # ---------- Communication threads -> UI ----------
    def ui(self, *msg):
        self.ui_queue.put(msg)

    def poll_ui_queue(self):
        try:
            while True:
                kind, *args = self.ui_queue.get_nowait()
                if kind == "status":
                    self.tree.set(args[0], "statut", args[1])
                elif kind == "title":
                    self.tree.set(args[0], "titre", args[1])
                elif kind == "log":
                    self.log(args[0])
                elif kind == "tick":
                    self.done += 1
                    self.progress["value"] = self.done
                elif kind == "finished":
                    self.running = False
                    self.start_btn.configure(state="normal")
                    self.stop_btn.configure(state="disabled")
                    self.log("— Terminé —")
        except queue.Empty:
            pass
        self.root.after(100, self.poll_ui_queue)

    # ---------- Contrôles ----------
    def start(self):
        if self.running:
            return
        raw = [u.strip() for u in self.url_text.get("1.0", "end").splitlines() if u.strip()]
        urls = list(dict.fromkeys(raw))  # enlève les doublons en gardant l'ordre
        if not urls:
            messagebox.showwarning("Aucune URL", "Colle au moins une URL YouTube.")
            return

        folder = self.folder_var.get().strip()
        try:
            os.makedirs(folder, exist_ok=True)
        except OSError as e:
            messagebox.showerror("Dossier invalide", str(e))
            return

        self.stop_event.clear()
        self.tree.delete(*self.tree.get_children())
        for i, url in enumerate(urls):
            self.tree.insert("", "end", iid=str(i), values=(url, "En attente"))

        self.total, self.done = len(urls), 0
        self.progress.configure(maximum=self.total, value=0)
        self.running = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        lang = None if self.lang_var.get() == "auto" else self.lang_var.get()
        threading.Thread(
            target=self.run_pipeline,
            args=(urls, folder, self.model_var.get(), lang, max(1, self.workers_var.get())),
            daemon=True,
        ).start()

    def stop(self):
        self.stop_event.set()
        self.log("Arrêt demandé… (les traitements en cours se terminent proprement)")

    def on_close(self):
        self.stop_event.set()
        self.root.destroy()

    # ---------- Pipeline ----------
    def run_pipeline(self, urls, folder, model_name, lang, workers):
        """Téléchargements en parallèle + transcription séquentielle (le CPU est
        le goulot d'étranglement : lancer plusieurs transcriptions en même temps
        ne va pas plus vite)."""
        tq = queue.Queue()
        transcriber = threading.Thread(
            target=self.transcriber, args=(tq, folder, model_name, lang), daemon=True)
        transcriber.start()

        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = [ex.submit(self.download, str(i), url, folder, tq)
                       for i, url in enumerate(urls)]
            for f in futures:
                f.result()

        tq.put(None)
        transcriber.join()
        self.ui("finished")

    def download(self, iid, url, folder, tq):
        if self.stop_event.is_set():
            self.ui("status", iid, "Annulé")
            self.ui("tick")
            return

        tmp_base = os.path.join(folder, f"temp_{uuid.uuid4().hex[:8]}")

        def hook(d):
            if self.stop_event.is_set():
                raise yt_dlp.utils.DownloadCancelled("Arrêt demandé")
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                if total:
                    pct = d["downloaded_bytes"] * 100 / total
                    self.ui("status", iid, f"Téléchargement {pct:.0f}%")

        opts = {
            "format": "bestaudio/best",
            "outtmpl": tmp_base + ".%(ext)s",
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "progress_hooks": [hook],
        }

        try:
            self.ui("status", iid, "Téléchargement…")
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
            title = info.get("title", "transcription")
            self.ui("title", iid, title)
            self.ui("status", iid, "En file de transcription")
            tq.put((iid, title, tmp_base + ".mp3"))
        except Exception as e:
            for leftover in glob.glob(tmp_base + "*"):
                try:
                    os.remove(leftover)
                except OSError:
                    pass
            if self.stop_event.is_set():
                self.ui("status", iid, "Annulé")
            else:
                self.ui("status", iid, "❌ Échec du téléchargement")
                self.ui("log", f"[{url}] {str(e)[:200]}")
            self.ui("tick")

    def transcriber(self, tq, folder, model_name, lang):
        model = None
        while True:
            job = tq.get()
            if job is None:
                break
            iid, title, audio = job
            try:
                if self.stop_event.is_set():
                    self.ui("status", iid, "Annulé")
                    continue

                if model is None:
                    self.ui("log", f"Chargement du modèle '{model_name}' (CPU, int8)…")
                    model = WhisperModel(model_name, device="cpu", compute_type="int8")

                self.ui("status", iid, "Transcription 0%")
                self.ui("log", f"Transcription : {title}")
                segments, info = model.transcribe(
                    audio, language=lang, beam_size=5, vad_filter=True)
                duration = info.duration or 0

                path = unique_path(folder, title)
                interrupted = False
                with open(path, "w", encoding="utf-8") as f:
                    for seg in segments:
                        if self.stop_event.is_set():
                            interrupted = True
                            break
                        f.write(seg.text.strip() + " ")
                        f.flush()
                        if duration:
                            self.ui("status", iid, f"Transcription {seg.end * 100 / duration:.0f}%")

                if interrupted:
                    self.ui("status", iid, "Interrompu (texte partiel sauvegardé)")
                else:
                    self.ui("status", iid, "✅ Terminé")
                    self.ui("log", f"Fichier créé : {path}")
            except Exception as e:
                self.ui("status", iid, "❌ Échec de la transcription")
                self.ui("log", f"[{title}] {str(e)[:200]}")
            finally:
                try:
                    os.remove(audio)
                except OSError:
                    pass
                self.ui("tick")


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
