# Scraibe

Scraibe is a local AI-powered meeting summarizer built with Flask, Ollama, and Whisper.

Users can:
- Paste meeting notes directly into the app
- Upload `.txt` meeting transcripts
- Upload `.mp3` recordings for transcription
- Generate AI summaries locally using Ollama
- Export summaries as TXT, DOCX, or PDF files

The project is designed to run fully locally without paid APIs.

---

# Features

- Local AI summarization with Ollama
- Audio transcription using Whisper
- Drag & drop file uploads
- TXT and MP3 support
- Markdown-style formatting
- DOCX export
- PDF export
- Loading states and upload validation

---

# Technologies Used

- Python
- Flask
- Ollama
- Whisper
- HTML/CSS/JavaScript
- python-docx
- ReportLab

---

# Requirements

Before running the project, install:

- Python 3.11+ recommended
- Ollama
- FFmpeg

---

# Installing Ollama

Download Ollama:

https://ollama.com/download

After installation, pull a model:

```bash
ollama pull gemma4
```

Or whichever model you want to use.

Then make sure Ollama is running:

```bash
ollama serve
```

---

# Installing FFmpeg (Required for MP3 Transcription)

Whisper requires FFmpeg for audio processing.

Download FFmpeg:

https://ffmpeg.org/download.html

After installing, ensure this works in your terminal:

```bash
ffmpeg -version
```

If it does not work, FFmpeg is likely not added to your system PATH.

---

# Installation

Clone the repository:

```bash
git clone d-floe/scraibe
cd scraibe
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the environment:

### Windows
```bash
.venv\Scripts\activate
```

### Mac/Linux
```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# Running the App

Start Flask:

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

---

# Supported File Types

- `.txt`
- `.mp3`

---

# Notes

- MP3 transcription may take time depending on audio length and hardware.
- The app temporarily stores uploaded files during processing and automatically deletes them afterward.
- AI summaries are generated locally through Ollama.

---

# Future Improvements

- Speaker identification
- Live recording support
- Streaming AI responses
- Better markdown rendering
- Improved PDF styling
- More export options

---

# License

This project is for educational purposes.
