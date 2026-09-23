#!/usr/bin/env python3
"""
Servidor Flask para gestionar reportes de Roca Port MDA47
Recibe PDFs y los sube a Google Drive automáticamente mediante API REST Directa
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import io
import json
import base64
import requests
import logging
import time
import jwt

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

def obtener_access_token(creds_dict):
    """Genera un token de acceso manual mediante una petición directa a Google Auth OAuth2"""
    try:
        ahora = int(time.time())
        payload = {
            "iss": creds_dict["client_email"],
            "sub": creds_dict["client_email"],
            "aud": "https://googleapis.com",
            "iat": ahora,
            "exp": ahora + 3600,
            "scope": "https://googleapis.com"
        }
        
        # Firma el JWT usando PyJWT con la llave privada del JSON de credenciales
        token_firmado = jwt.encode(payload, creds_dict["private_key"], algorithm="RS256")
        
        # Solicita el token de acceso real a Google
        url_token = "https://googleapis.com"
        data_token = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": token_firmado
        }
        
        res = requests.post(url_token, data=data_token, timeout=10)
        return res.json().get("access_token")
    except Exception as e:
        logger.error(f"❌ Error al generar token OAuth2: {e}")
        return None

@app.route('/api/upload-pdf', methods=['POST', 'OPTIONS'])
def upload_pdf():
    """Recibe el PDF en base64 del nuevo formulario y lo sube por HTTP REST Multipart"""
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        pdf_base64 = data.get('pdf')
        filename = data.get('filename', 'reporte.pdf')
        
        if not pdf_base64:
            return jsonify({'error': 'No PDF data provided'}), 400
            
        # Convertir base64 a bytes
        if ',' in pdf_base64:
            pdf_base64 = pdf_base64.split(',')[1]
        pdf_bytes = base64.b64decode(pdf_base64)
        
        # Cargar credenciales del archivo secreto de Render
        ruta_secreto = '/etc/secrets/google-creds.json'
        with open(ruta_secreto, 'r') as f:
            creds_dict = json.load(f)
            
        # Obtener token de acceso fresco y válido
        access_token = obtener_access_token(creds_dict)
        if not access_token:
            return jsonify({'error': 'No se pudo autenticar con Google (Token Fallido)'}), 500
            
        # 📤 SUBIDA MULTIPART REAL A GOOGLE DRIVE API V3
        url = "https://googleapis.com"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        metadata = {
            'name': filename,
            'parents': [DRIVE_FOLDER_ID]
        }
        
        files = {
            'data': ('metadata', json.dumps(metadata), 'application/json'),
            'file': (filename, io.BytesIO(pdf_bytes), 'application/pdf')
        }
        
        logger.info(f"📤 Transmitiendo PDF real a la carpeta de Drive: {filename}...")
        respuesta_drive = requests.post(url, headers=headers, files=files, timeout=30)
        
        if respuesta_drive.status_code != 200:
            logger.error(f"❌ Fallo de Drive API: {respuesta_drive.text}")
            return jsonify({'error': f'Google Drive rechazó el archivo: {respuesta_drive.text}'}), respuesta_drive.status_code
            
        resultado_json = respuesta_drive.json()
        file_id = resultado_json.get('id')
        logger.info(f"✅ Archivo guardado físicamente en Drive con ID: {file_id}")
        
        return jsonify({
            'success': True,
            'message': f'Reporte guardado exitosamente en Drive: {filename}',
            'fileId': file_id,
            'link': f'https://google.com{DRIVE_FOLDER_ID}'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error crítico al procesar subida: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health():
    if request.method == 'OPTIONS':
        return '', 204
    return jsonify({'status': 'ok'}), 200

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'servidor': 'Reporte Roca Port MDA47',
        'version': '1.4',
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
