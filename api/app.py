import os
import uuid
import tempfile
from flask import Flask, request, jsonify
import fitz  # PyMuPDF
from docx import Document
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
# Temporary in-memory dictionary to store extracted texts.
# Note: For production with heavy traffic, replace this with Redis or a database (SQLite/PostgreSQL)
EXTRACTED_STORE = {}

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_and_extract(file):
    """Saves the uploaded file temporarily, extracts text, and deletes the file."""
    ext = file.filename.rsplit('.', 1)[1].lower()
    
    # Create a temporary file on the server
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
        # Clean up: Always delete the temporary file after extraction
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
    return extracted_text

@app.route('/upload', methods=['POST'])
def upload_file():
    # 1. Check if the request contains a file
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
        
    file = request.files['file']
    
    # 2. Check if the user actually selected a file
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    # 3. Process the file if it has an allowed extension
    if file and allowed_file(file.filename):
        text = process_and_extract(file)
        
        # Generate a unique tracking ID for this extraction
        text_id = str(uuid.uuid4())
        
        # Store the text temporarily
        EXTRACTED_STORE[text_id] = text
        
        return jsonify({
            "message": "File successfully uploaded and extracted.",
            "text_id": text_id,
            "filename": file.filename
        }), 200
        
    return jsonify({"error": "Unsupported file format. Please upload .txt, .pdf, or .docx"}), 400

@app.route('/extracted/<text_id>', methods=['GET'])
def get_extracted_text(text_id):
    """Endpoint for other apps (or the frontend) to fetch the extracted text."""
    if text_id in EXTRACTED_STORE:
        return jsonify({
            "text_id": text_id,
            "content": EXTRACTED_STORE[text_id]
        }), 200
        
    return jsonify({"error": "Text not found or has expired."}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)