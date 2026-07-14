import os
import uuid
import tempfile
import asyncio
from flask import Flask, request, jsonify, send_file
import fitz  # PyMuPDF
from docx import Document
from flask_cors import CORS
import edge_tts  # 🌟 Replaced gTTS with edge-tts

app = Flask(__name__)
CORS(app)

# Temporary in-memory dictionary to store extracted texts.
EXTRACTED_STORE = {}
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

# Global path definition for the temporary output file
AUDIO_OUTPUT_PATH = os.path.join(tempfile.gettempdir(), "generated_podcast.mp3")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_and_extract(file):
    """Saves the uploaded file temporarily, extracts text, and deletes the file."""
    ext = file.filename.rsplit('.', 1)[1].lower()
    
    fd, temp_path = tempfile.mkstemp(suffix=f\".{ext}\")
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
                extracted_text += page.get_text()
                
        elif ext == 'docx':
            doc = Document(temp_path)
            extracted_text = "\n".join([p.text for p in doc.paragraphs])
            
    finally:
        os.remove(temp_path)
        
    return extracted_text

# 🌟 HELPER FUNCTION TO RUN ASYNC EDGE-TTS INSIDE FLASK
def run_edge_tts(text, output_path, voice="en-US-EmmaNeural"):
    async def amain():
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
    
    # Run the async loop synchronously for the Flask worker thread
    asyncio.run(amain())

# ============================================================
# NEW REPLACED EDGE-TTS AUDIO GENERATION ENDPOINT
# ============================================================
@app.route('/generate-audio/<text_id>', methods=['POST'])
def generate_audio_endpoint(text_id):
    print(f"🎵 Received audio generation request for text_id: {text_id}")
    
    if text_id not in EXTRACTED_STORE:
        print(f"❌ Error: text_id {text_id} not found in store.")
        return jsonify({"error": "Invalid or missing text_id"}), 404

    text_to_convert = EXTRACTED_STORE[text_id]
    
    # Simple fallback check if text payload is empty
    if not text_to_convert.strip():
        text_to_convert = "The document layout was processed, but no readable text could be extracted."

    try:
        print("⏳ Generating premium streaming audio via Microsoft Neural Engine...")
        
        # Clean up any leftover file if it exists from a previous generation run
        if os.path.exists(AUDIO_OUTPUT_PATH):
            os.remove(AUDIO_OUTPUT_PATH)

        # Generate audio using edge-tts
        run_edge_tts(text_to_convert, AUDIO_OUTPUT_PATH, voice="en-US-EmmaNeural")
        
        print(f"✅ Premium Neural Audio successfully saved to: {AUDIO_OUTPUT_PATH}")
        
        return send_file(
            AUDIO_OUTPUT_PATH,
            mimetype="audio/mpeg",
            as_attachment=True,
            download_name="generated_podcast.mp3"
        )

    except Exception as e:
        print(f"❌ Cloud TTS Generation Error: {str(e)}")
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
            "text": EXTRACTED_STORE[text_id]
        }), 200
    return jsonify({"error": "Text ID not found"}), 404

if __name__ == '__main__':
    # Cloud-friendly local testing initialization
    app.run(host='0.0.0.0', port=5000, debug=True)