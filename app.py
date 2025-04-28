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

        # Vérification plus intelligente : vérifier le contenu, pas juste l'extension
        try:
            reader = PyPDF2.PdfReader(file.stream)
            if len(reader.pages) == 0:
                raise Exception("Pas de pages dans le fichier PDF")
            file.stream.seek(0)  # Revenir au début du fichier après lecture
        except Exception as e:
            return jsonify({'error': f'Le fichier {file.filename or "inconnu"} n\'est pas un PDF valide ({str(e)})'}), 400

    merge_id = str(uuid.uuid4())
    file_paths = []

    for file in files:
        # Si pas d'extension .pdf dans le nom, on ajoute manuellement
        filename = secure_filename(file.filename)
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'

        file_path = os.path.join(UPLOAD_FOLDER, f"{merge_id}_{filename}")
        file.save(file_path)
        file_paths.append(file_path)

    merger = PyPDF2.PdfMerger()
    try:
        for file_path in file_paths:
            merger.append(file_path)

        output_path = os.path.join(UPLOAD_FOLDER, f"{merge_id}_merged.pdf")
        merger.write(output_path)

        return send_file(
            output_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='merged.pdf'
        )

    except Exception as e:
        return jsonify({'error': f'Erreur lors de la fusion: {str(e)}'}), 500

    finally:
        # Nettoyage des fichiers temporaires
        for file_path in file_paths:
            try:
                os.remove(file_path)
            except:
                pass
        try:
            merger.close()
        except:
            pass

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
