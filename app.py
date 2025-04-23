from flask import Flask, request, send_file, jsonify
import PyPDF2
import os
from werkzeug.utils import secure_filename
import tempfile
import uuid

app = Flask(__name__)

UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/merge-pdfs', methods=['POST'])
def merge_pdfs():
    if 'files' not in request.files:
        return jsonify({'error': 'Aucun fichier trouvé'}), 400

    files = request.files.getlist('files')

    if len(files) < 2:
        return jsonify({'error': 'Veuillez fournir au moins deux fichiers PDF à fusionner'}), 400

    for file in files:
        if file.filename == '':
            return jsonify({'error': 'Un ou plusieurs fichiers n\'ont pas de nom'}), 400
        if not allowed_file(file.filename):
            return jsonify({'error': f'Le fichier {file.filename} n'est pas un PDF'}), 400

    merge_id = str(uuid.uuid4())
    file_paths = []

    for file in files:
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, f"{merge_id}_{filename}")
        file.save(file_path)
        file_paths.append(file_path)

    merger = PyPDF2.PdfMerger()
    try:
        for file_path in file_paths:
            merger.append(file_path)

        output_path = os.path.join(UPLOAD_FOLDER, f"{merge_id}_merged.pdf")
        merger.write(output_path)
        merger.close()

        for file_path in file_paths:
            try:
                os.remove(file_path)
            except:
                pass

        return send_file(output_path,
                         mimetype='application/pdf',
                         as_attachment=True,
                         download_name='merged.pdf')

    except Exception as e:
        for file_path in file_paths:
            try:
                os.remove(file_path)
            except:
                pass
        return jsonify({'error': f'Erreur lors de la fusion: {str(e)}'}), 500
    finally:
        try:
            merger.close()
        except:
            pass

if __name__ == '__main__':
    app.run(debug=True)
