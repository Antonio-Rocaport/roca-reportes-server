#!/usr/bin/env python3
"""
Servidor Flask para gestionar reportes de Roca Port MDA47
Reenvía el PDF directamente a Google Apps Script para evitar bloqueos de tokens
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import logging
import os

app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "*"}}, allow_headers=["Content-Type"], methods=["GET", "POST", "OPTIONS"])

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🔗 TU ENLACE DE GOOGLE APPS SCRIPT INSTALADO Y LISTO
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbx04ynRdCg4TvW4MTj6DCcr1HCrV_Gl5EfLXdQNa7aCytZpydB6YyFhL36LRUzvKjK1/exec"

@app.route('/api/upload-pdf', methods=['POST', 'OPTIONS'])
def upload_pdf():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.json
        if not data or 'pdf' not in data:
            return jsonify({'error': 'No PDF data provided'}), 400
            
        filename = data.get('filename', 'reporte.pdf')
        logger.info(f"🚀 Reenviando {filename} por puente libre de Apps Script...")
        
        # Le enviamos el archivo directo a Google sin usar las librerías rotas de tokens
        respuesta = requests.post(URL_GOOGLE_SCRIPT, json=data, timeout=30)
        
        return jsonify(respuesta.json()), respuesta.status_code
        
    except Exception as e:
        logger.error(f"❌ Error en el puente: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health():
    if request.method == 'OPTIONS':
        return '', 204
    return jsonify({'status': 'ok'}), 200

@app.route('/reporte')
def servir_reporte():
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return jsonify({'error': 'Archivo index.html no encontrado'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
