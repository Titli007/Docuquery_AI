import os
from flask import Flask, request, jsonify
from document_processor import DocumentProcessor
from chat_service import chat_blueprint  # Import the blueprint

app = Flask(__name__)

document_processor = DocumentProcessor()

@app.route('/api/documents/process', methods=['POST'])
def process_document():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    file_path = os.path.join(document_processor.temp_dir, file.filename)
    file.save(file_path)

    file_type = file.filename.split(".")[-1]
    asset_id = document_processor.process_document(file_path, file_type)

    return jsonify({"asset_id": asset_id}), 201

# Register the chat blueprint
app.register_blueprint(chat_blueprint)

if __name__ == '__main__':
    app.run(debug=True)
