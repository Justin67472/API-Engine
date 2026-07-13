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
# NEW ENDPOINT: GENERATE PODCAST AUDIO FROM POLISHED TEXT
# ============================================================
@app.route('/generate-podcast', methods=['POST'])
def generate_podcast():
    try:
        # 1. Parse JSON payload sent from the React Native app
        data = request.get_json() or {}
        text_to_speak = data.get("text")
        
        if not text_to_speak:
            return jsonify({"error": "No text provided in the request body"}), 400
        
        print(f"⏳ Forwarding text to ElevenLabs: {text_to_speak[:40]}...")

        # 2. Request TTS from ElevenLabs using the verified free Rachel ID
        audio_response = client.text_to_speech.convert(
            text=text_to_speak,
            voice_id="Xb7hH8MSUJpSbSDYk0k2",  # Rachel (Free Tier Friendly)
            model_id="eleven_multilingual_v2"
        )
        
        # 3. Stream incoming chunks into our audio path destination
        with open(AUDIO_OUTPUT_PATH, "wb") as f:
            for chunk in audio_response:
                if chunk:
                    f.write(chunk)
                    
        print("✅ MP3 generation finalized. Dispatching file back to the application...")

        # 4. Stream the raw file attachment back to the Expo frontend
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