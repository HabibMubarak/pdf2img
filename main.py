import os
import tempfile
from flask import Flask, request, jsonify, render_template, send_file, send_from_directory
import pdfplumber
from io import BytesIO
import base64

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert_pdf_to_images', methods=['POST'])
def convert_pdf_to_images():
    if 'pdf_file' not in request.files:
        return jsonify({'error': 'Bitte eine PDF-Datei hochladen!'}), 400

    pdf_file = request.files['pdf_file']
    use_temp = request.args.get('use_temp', 'true').lower() == 'true'
    return_bytes = request.args.get('return_bytes', 'false').lower() == 'true'
    expects_html = 'text/html' in request.headers.get('Accept', '')

    images = []
    image_bytes = []  # Speicher für Bild-Bytes

    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page_num, page in enumerate(pdf.pages):
                img = page.to_image(resolution=300)

                if return_bytes:
                    img_io = BytesIO()
                    img.original.save(img_io, format='PNG')
                    img_io.seek(0)
                    # Base64-Kodierung für JSON-kompatible Übertragung
                    img_base64 = base64.b64encode(img_io.read()).decode("utf-8")
                    image_bytes.append(img_base64)

                elif use_temp:
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                    img.original.save(temp_file, format='PNG')
                    temp_file.close()
                    images.append(temp_file.name)

        if return_bytes:
            return jsonify({'image_bytes': image_bytes})  # Base64-kodierte Bilder zurückgeben


        if expects_html:
            return render_template('result.html', image_urls=[f"/get_image?path={img}" for img in images])
        else:
            return jsonify({'image_urls': [f"/get_image?path={img}" for img in images]} if use_temp else {'image_paths': images})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get_image', methods=['GET'])
def get_image():
    image_path = request.args.get('path')
    if not image_path:
        return jsonify({'error': 'Bildpfad nicht angegeben!'}), 400

    try:
        return send_file(image_path, mimetype='image/png')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)