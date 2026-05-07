# Import Flask (the web framework), render_template (to load HTML), and request (to access data sent from the user)
from flask import Flask, render_template, request

# requests lets us send HTTP requests (we'll use it to talk to Ollama)
import requests

# transcription model
import whisper
whisper_model = whisper.load_model("tiny")

# Create the Flask App
#__name__ tells Flask where to look for files like templates
app = Flask(__name__)

def transcribe_audio(file_path):
    """
    Takes an audio file path and returns transcribed text using Whisper
    """
    result = whisper_model.transcribe(file_path)
    return result["text"]

# Function for loading prompt file
def load_prompt(file_path):
    with open(file_path, "r") as file:
        return file.read()


# This function sends user text to Ollama and gets a summary back
def summarize_with_ollama(text):
    try:
        # Loads prompt from file path
        prompt_template = load_prompt("prompts/summarize.txt")

        # Replace placeholder with actual notes
        prompt = prompt_template.format(notes=text)

        # print("---- PROMPT BEING SENT ----")
        # print(prompt)
        # print("--------------------------")

        # Send a POST request to Ollama's local API
        # This runs locally at 11434
        response = requests.post(
            "http://localhost:11434/api/generate",
            
            json={
                # The model you're using (must be pulled already)
                "model": "gemma4",
            
                # The prompt tells the AI exactly what to do
                "prompt": prompt,

                # stream=False means we wait for the full response at once
                # (simpler for beginners)
                "stream": False
            }
        )
        
        # Convert the response into JSON (Python disctionary)
        data = response.json()

        # Extract the actual AI-generated text
        # if something goes wrong, return a fallback message
        return data.get("response", "No response from model.")
    
    except Exception as e:
        
        # If the request fails (e.g., Ollama not running)
        # return an error message instead of crashing the app
        return f"Error connecting to Ollama: {e}"


# Define a route (URL endpoint)
# "/" means the homepage (http://127.0.0.1:5000/)
# methods=["GET", "POST"] means this page can both display and recieve from data
@app.route("/", methods=["GET", "POST"])
def index():

    # This will store the output we send back to the webpage
    response = ""

    # Check if the user submitted the form
    # "POST" happens when the user clicks the submit button
    if request.method == "POST":

        # Get the text from the textarea in the HTML form
        # "notes" must match the name attribute in your HTML <textarea>
        user_input = request.form.get("notes")

        # Only process if the user actually entered something
        if user_input:
            
            #Send the input to Ollama and get a summary back
            response = summarize_with_ollama(user_input)

    # Renders the HTML page (index.html)
    # We pass the "response" variable into the template so it can be displayed using {{ response}}
    return render_template("index.html", response=response)


# ==================IMPORTING==================
from werkzeug.utils import secure_filename
import os
from flask import flash, redirect

# Maximum upload size (in byes)
# 16 MB is plenty for small MP3s and text files
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

@app.errorhandler(413)
def file_too_large(error):
    """
    Handles files that exceel MAX_CONTENT_LENGTH
    """
    return render_template (
        "index.html",
        error="File is too large. Maximum size is 16 MB"
    )

ALLOWED_EXTENSIONS = {"txt", "mp3"}

def allowed_file(filename):
    """
    Checks if uploaded file has an allowed extension
    """

    #ensure filename has a period
    if "." not in filename:
        return False
    
    # Get extension after final period
    extension = filename.rsplit(".", 1)[1].lower()

    return extension in ALLOWED_EXTENSIONS

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/upload", methods=["POST"])
def upload_file():

    file = request.files.get("file")

    # No file selected
    if not file or file.filename == "":
        return render_template(
            "index.html",
            error="Please select a file."
        )

    # Invalid file type
    if not allowed_file(file.filename):
        return render_template(
            "index.html",
            error="Unsupported file type. Please upload a TXT or MP3 file."
        )

    filename = secure_filename(file.filename)

    file_path = os.path.join(UPLOAD_FOLDER, filename)

    file.save(file_path)

    try:
        # TXT processing
        if filename.endswith(".txt"):

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

        # MP3 transcription
        elif filename.endswith(".mp3"):

            content = transcribe_audio(file_path)

        # Summarize
        response = summarize_with_ollama(content)

        return render_template(
            "index.html",
            response=response,

            # Pass uploaded/transcribed text
            original_text=content,

            error=None
        )
    
    finally:
        # CLEAN UP TEMP FILE
        # Delete uploaded file after processing
        if os.path.exists(file_path):
            os.remove(file_path)


# =================EXPORTING===================


# Import tools for file creation and sending downloads
from flask import send_file
import io # allows us to create files in memory (no disk needed)

# For PDF creation
from docx import Document

# For PDF creation
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Spacer

import re #for detecting **bold**

def parse_markdown(text):
    """
    Parses markdown-like text into structured elements.
    """
    lines = text.split("\n")
    parsed = []

    for line in lines:
        # Ensure it's a string
        if not isinstance(line, str):
            continue

        line = line.strip()

        if not line:
            continue

        # Remove markdown heading symbols like ## or ###
        clean_line = re.sub(r"^#+\s*", "", line)

        # Remove trailing colon and extra whitespace
        clean_line = clean_line.strip().rstrip(":")

        lower = clean_line.lower()
        
        if any(keyword in lower for keyword in [
            "summary",
            "key decisions",
            "action items"]):
            parsed.append(("heading", clean_line))

        # Detect bullet points
        elif line.startswith("-") or line.startswith("•"):
            parsed.append(("bullet", line.lstrip("-• ").strip()))
        
        # Default: paragraph
        else: 
            parsed.append(("paragraph", clean_line))
        
    return parsed
    

# Route to export as TXT
@app.route ("/export/txt", methods=["POST"])
def export_txt():
    # Get markdown text from frontend
    content = request.form.get("content", "")

    # Create in-memory text file
    buffer = io.BytesIO()
    buffer.write(content.encode("utf-8"))
    buffer.seek(0)

    # Send file as download
    return send_file(
        buffer,
        as_attachment=True,
        download_name="meeting_notes.txt",
        mimetype="text/plain"
    )

# Route to export as DOCX
def add_bold_runs(paragraph, text):
    """
    Splits text by **bold** markers and applies formatting.
    Example: "Hello **world**" -> normal + bold run
    """
    parts = re.split(r"(\*\*.*?\*\*)", text)

    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2]) # remove **
            run.bold = True
        else:
            paragraph.add_run(part)


@app.route("/export/docx", methods=["POST"])
def export_docx():
    content = request.form.get("content", "")

    # Parse markdown into structured format
    parsed = parse_markdown(content)

    # Create a Word document
    doc = Document()

    # Add Parsed content
    for item_type, text in parsed:
        if item_type == "heading":
            # Add heading (level 2 looks nice)
            doc.add_heading(text, level=2)
            
        elif item_type == "bullet":
            # Add bullet point
            p = doc.add_paragraph(style = "List Bullet")
            add_bold_runs(p, text)

        elif item_type == "paragraph":
            # Normal paragraph
            p = doc.add_paragraph()
            add_bold_runs(p, text)

    # Save to memory instead of disk
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="meeting_notes.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

# Route to export as PDF
def convert_bold_to_html(text):
    """
    Converts **bold** -> <b>bold</b> for PDF rendering
    """
    return re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)

@app.route("/export/pdf", methods=["POST"])
def export_pdf():
    content = request.form.get("content", "")

    parsed = parse_markdown(content)

    buffer = io.BytesIO()

    # Create PDF document
    doc = SimpleDocTemplate(buffer)

    styles =  getSampleStyleSheet()

    # Convert text into Paragraph (basic formatting)
    story = []

    for item_type, text in parsed:

        text = convert_bold_to_html(text)
        
        if item_type == "heading":
            # Use a larger bold style
            story.append(Paragraph(f"<b>{text}</b>", styles["Heading2"]))
            story.append(Spacer(1, 10))

        elif item_type == "bullet":
            # Add bullet manually
            story.append(Paragraph(f"• {text}", styles ["Normal"]))
            story.append(Spacer(1, 6))
        
        elif item_type == "paragraph":
            story.append(Paragraph(text, styles["Normal"]))
            story.append(Spacer(1, 8))

        #Add spacing after each element
        story.append(Paragraph("<br/>", styles ["Normal"]))

    # Build PDF
    doc.build(story)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="Meeting_notes.pdf",
        mimetype="application/pdf"
    )

# ================
# KEEP THIS AT THE BOTTOM
# =================

# This ensures the app only runs when you execute this file directly
# (not when it's imported somewhere else)
if __name__ == "__main__":
    
    # Run the Flask development server. debug=True means auto-restarts when save changes and shows helpful error messages
    app.run(debug=True)