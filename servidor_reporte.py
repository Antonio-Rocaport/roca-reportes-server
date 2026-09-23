#!/usr/bin/env python3
"""
Servidor Flask para gestionar reportes de Roca Port MDA47
Recibe PDFs y los sube a Google Drive automáticamente usando la librería oficial robusta
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import os
import io
import json
import base64
import logging

app = Flask(__name__)

# ⭐ CONFIGURAR CORS CORRECTAMENTE
CORS(app, 
     resources={r"/api/*": {"origins": "*"}},
     allow_headers=["Content-Type"],
     methods=["GET", "POST", "OPTIONS"])

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Max-Age'] = '3600'
    return response

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ID de tu carpeta Drive
DRIVE_FOLDER_ID = "1bu93DnzhCZuVic-kE85xFl4LXeeHXL4P"

# Variables globales para el servicio de Drive
drive_service = None

def inicializar_drive():
    """Inicializa la conexión oficial y robusta usando el archivo secreto de Render"""
    global drive_service
    try:
        ruta_secreto = '/etc/secrets/google-creds.json'
        logger.info(f"🔍 Cargando credenciales oficiales desde: {ruta_secreto}")
        
        if not os.path.exists(ruta_secreto):
            logger.error(f"❌ Archivo no encontrado en Render: {ruta_secreto}")
            return False
            
        # La librería oficial lee el JSON directamente de forma segura
        credentials = Credentials.from_service_account_file(
            ruta_secreto,
            scopes=['https://googleapis.com']
        )
        
        drive_service = build('drive', 'v3', credentials=credentials)
        logger.info("✅ Conexión con Google Drive establecida de forma segura e interna")
        return True
    except Exception as e:
        logger.error(f"❌ Error crítico de inicialización de Drive: {e}", exc_info=True)
        return False

# Inicializar conexión al arrancar el servidor
inicializar_drive()

@app.route('/api/upload-pdf', methods=['POST', 'OPTIONS'])
def upload_pdf():
    """Recibe el PDF en base64 del formulario y lo sube de forma real a la carpeta de Drive"""
    if request.method == 'OPTIONS':
        return '', 204
    
    global drive_service
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        pdf_base64 = data.get('pdf')
        filename = data.get('filename', 'reporte.pdf')
        
        if not pdf_base64:
            return jsonify({'error': 'No PDF data provided'}), 400
            
        # Re-inicializar si por alguna razón se perdió el servicio en Render
        if not drive_service:
            if not inicializar_drive():
                return jsonify({'error': 'Servicio de Google Drive no disponible en el servidor'}), 500
        
        # Convertir base64 a bytes
        if ',' in pdf_base64:
            pdf_base64 = pdf_base64.split(',')[1]
        pdf_bytes = base64.b64decode(pdf_base64)
        
        # Estructurar metadatos del archivo destino
        file_metadata = {
            'name': filename,
            'parents': [DRIVE_FOLDER_ID]
        }
        
        media = MediaIoBaseUpload(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            resumable=True
        )
        
        logger.info(f"📤 Transmitiendo archivo real a Drive: {filename}...")
        
        # Subida oficial forzando el almacenamiento compartido absorbiendo tu cuenta
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink',
            supportsAllDrives=True
        ).execute()
        
        file_id = file.get('id')
        logger.info(f"✅ Archivo guardado físicamente en Drive con ID: {file_id}")
        
        return jsonify({
            'success': True,
            'message': f'Reporte guardado exitosamente en Drive: {filename}',
            'fileId': file_id,
            'link': file.get('webViewLink')
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error en la subida del PDF: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health():
    if request.method == 'OPTIONS':
        return '', 204
    drive_ok = drive_service is not None
    return jsonify({'status': 'ok', 'drive_connected': drive_ok}), 200

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'servidor': 'Reporte Roca Port MDA47',
        'version': '1.5',
        'endpoints': {'/api/upload-pdf': 'POST', '/api/health': 'GET', '/reporte': 'GET'}
    }), 200

@app.route('/reporte')
def servir_reporte():
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return jsonify({'error': 'Archivo index.html no encontrado'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
