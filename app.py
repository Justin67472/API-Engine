from flask import Flask, request, jsonify
import fitz  # PyMuPDF
from docx import Document
import os
import tempfile

app = Flask(__name__)

@app.route('/api/extract', methods=['POST'])
def extract():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    ext = file.filename.split('.')[-1].lower()
    
    # Save to a temporary file
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
    file.save(temp.name)
    
    text = ""
    try:
        if ext == 'pdf':
            doc = fitz.open(temp.name)
            for page in doc:
                text += page.get_text() + "\n"
        elif ext == 'docx':
            doc = Document(temp.name)
            text = "\n".join([para.text for para in doc.paragraphs])
        elif ext == 'txt':
            with open(temp.name, 'r', encoding='utf-8') as f:
                text = f.read()
    finally:
        os.remove(temp.name) # Cleanup
        
    return jsonify({"content": text})

if __name__ == '__main__':
    app.run(debug=True)