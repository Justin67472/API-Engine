import os
import uuid
import tempfile
from flask import Flask, request, jsonify, send_file
import fitz  # PyMuPDF
from docx import Document
from flask_cors import CORS
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
CORS(app)

# Temporary in-memory dictionary to store extracted texts.
EXTRACTED_STORE = {}
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

# Initialize ElevenLabs Client using the loaded environment key
api_key = os.getenv("ELEVENLABS_API_KEY")
client = ElevenLabs(api_key=api_key)

# Global path definition for the temporary output file
AUDIO_OUTPUT_PATH = os.path.join(tempfile.gettempdir(), "generated_podcast.mp3")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_and_extract(file):
    """Saves the uploaded file temporarily, extracts text, and deletes the file."""
    ext = file.filename.rsplit('.', 1)[1].lower()
    
    fd, temp_path = tempfile.mkstemp(suffix=f".{ext}")
    os.close(fd)
    file.save(temp_path)
    
    extracted_text = ""
    try:
        if ext == 'txt':
            with open(temp_path, 'r', encoding='utf-8') as f:
                extracted_text = f.read()
                
        elif ext == 'pdf':
            doc = fitz.open(temp_path)
            for page in doc:
                extracted_text += page.get_text() + "\n"
                
        elif ext == 'docx':
            doc = Document(temp_path)
            extracted_text = "\n".join([para.text for para in doc.paragraphs])
            
    except Exception as e:
        extracted_text = f"An error occurred during extraction: {str(e)}"
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
    return extracted_text
# ============================================================
# UPDATED ENDPOINT: HANDLES LARGE TEXTS BY CHUNKING
# ============================================================
@app.route('/generate-podcast', methods=['POST'])
def generate_podcast():
    try:
        data = request.get_json() or {}
        text_to_speak = data.get("text")
        
        if not text_to_speak:
            return jsonify({"error": "No text provided in the request body"}), 400
        
        # 1. Break text down into safety blocks under ElevenLabs' 10,000 limit
        MAX_CHARS = 8000  # 8k keeps a safe margin away from the hard 10k ceiling
        text_chunks = [text_to_speak[i:i + MAX_CHARS] for i in range(0, len(text_to_speak), MAX_CHARS)]
        
        print(f"⏳ Text length: {len(text_to_speak)} characters. Split into {len(text_chunks)} payload chunk(s).")

        # 2. Open our temporary output file in binary write mode
        with open(AUDIO_OUTPUT_PATH, "wb") as f:
            for idx, chunk in enumerate(text_chunks):
                print(f"🎙️ Processing chunk {idx + 1}/{len(text_chunks)} ({len(chunk)} chars)...")
                
                # Fetch TTS bytes for the current text slice
                audio_response = client.text_to_speech.convert(
                    text=chunk,
                    voice_id="Xb7hH8MSUJpSbSDYk0k2",  # Rachel Free Tier
                    model_id="eleven_multilingual_v2"
                )
                
                # Stream the binary chunks right into the single combined file
                for audio_bytes in audio_response:
                    if audio_bytes:
                        f.write(audio_bytes)
                        
        print("✅ Combined MP3 generation finalized. Dispatching file back to application...")

        # 3. Stream the raw file attachment back to the Expo frontend
        return send_file(
            AUDIO_OUTPUT_PATH,
            mimetype="audio/mpeg",
            as_attachment=True,
            download_name="podcast.mp3"
        )

    except Exception as e:
        print(f"❌ Audio API Generation Error: {str(e)}")
        return jsonify({"error": str(e)}), 500
# ============================================================
# EXISTING EXTRACTION ENDPOINTS
# ============================================================
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    if file and allowed_file(file.filename):
        text = process_and_extract(file)
        text_id = str(uuid.uuid4())
        EXTRACTED_STORE[text_id] = text
        
        return jsonify({
            "message": "File successfully uploaded and extracted.",
            "text_id": text_id,
            "filename": file.filename
        }), 200
        
    return jsonify({"error": "Unsupported file format. Please upload .txt, .pdf, or .docx"}), 400

@app.route('/extracted/<text_id>', methods=['GET'])
def get_extracted_text(text_id):
    if text_id in EXTRACTED_STORE:
        return jsonify({
            "text_id": text_id,
            "content": EXTRACTED_STORE[text_id]
        }), 200
    return jsonify({"error": "Text not found or has expired."}), 404

if __name__ == '__main__':
    # Binding to 0.0.0.0 makes the API visible to your local network/Expo development tools
    app.run(host='0.0.0.0', port=5000, debug=True)