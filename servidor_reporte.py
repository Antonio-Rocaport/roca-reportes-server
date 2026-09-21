#!/usr/bin/env python3
"""
Servidor Flask para gestionar reportes de Roca Port MDA47
Recibe PDFs y los sube a Google Drive automáticamente
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2.service_account import Credentials
import os
import io
import json
import base64
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import logging

app = Flask(__name__)
CORS(app)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ID de tu carpeta Drive
DRIVE_FOLDER_ID = "1bu93DnzhCZuViC-kE85xFl4LXeeHXL4P"

# Variables globales para credenciales
drive_service = None
credentials = None

def inicializar_drive():
    """Inicializa conexión a Google Drive"""
    global drive_service, credentials
    try:
        ruta_secreto = '/etc/secrets/google-creds.json'
        logger.info(f"🔍 Buscando credenciales en: {ruta_secreto}")
        
        # Verificar si el archivo existe
        if not os.path.exists(ruta_secreto):
            logger.error(f"❌ Archivo no encontrado: {ruta_secreto}")
            return False
        
        # Leer archivo
        with open(ruta_secreto, 'r') as f:
            creds_json = f.read()
        
        if not creds_json:
            logger.error("❌ Archivo de credenciales vacío")
            return False
        
        # Parsear JSON
        creds_dict = json.loads(creds_json)
        
        # Crear credenciales
        credentials = Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/drive.file']
        )
        
        # Construir servicio
        drive_service = build('drive', 'v3', credentials=credentials)
        logger.info("✅ Google Drive conectado correctamente")
        return True
        
    except FileNotFoundError:
        logger.error(f"❌ Archivo no encontrado: {ruta_secreto}")
        return False
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error al parsear JSON: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error al conectar Drive: {e}", exc_info=True)
        return False

# ⭐ INICIALIZAR DRIVE APENAS SE CARGA LA APP (fuera de if __name__)
logger.info("🚀 Inicializando Drive...")
if not inicializar_drive():
    logger.warning("⚠️ Drive no inicializado al inicio")

@app.route('/api/upload-pdf', methods=['POST'])
def upload_pdf():
    """Recibe PDF en base64 y lo sube a Drive"""
    try:
        data = request.json
        pdf_base64 = data.get('pdf')
        filename = data.get('filename', 'reporte.pdf')
        
        if not pdf_base64:
            return jsonify({'error': 'No PDF data provided'}), 400
        
        if not drive_service:
            return jsonify({'error': 'Drive no inicializado'}), 500
        
        # Convertir base64 a bytes
        pdf_bytes = base64.b64decode(pdf_base64.split(',')[1] if ',' in pdf_base64 else pdf_base64)
        
        # Crear archivo en Drive
        file_metadata = {
            'name': filename,
            'parents': [DRIVE_FOLDER_ID]
        }
        
        media = MediaIoBaseUpload(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            resumable=True
        )
        
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        logger.info(f"✅ PDF subido: {filename} (ID: {file.get('id')})")
        
        return jsonify({
            'success': True,
            'message': f'Reporte guardado en Drive: {filename}',
            'fileId': file.get('id'),
            'link': file.get('webViewLink')
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error al subir PDF: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Verificar que el servidor está corriendo"""
    drive_ok = drive_service is not None
    return jsonify({
        'status': 'ok',
        'drive_connected': drive_ok
    }), 200

@app.route('/', methods=['GET'])
def index():
    """Página de inicio"""
    return jsonify({
        'servidor': 'Reporte Roca Port MDA47',
        'version': '1.0',
        'endpoints': {
            '/api/upload-pdf': 'POST - Subir PDF a Drive',
            '/api/health': 'GET - Verificar estado'
        }
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV', 'production') == 'development'
    logger.info(f"🚀 Servidor iniciado en puerto {port}")
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode,
        use_reloader=False
    )
