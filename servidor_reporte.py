import os
import json
from datetime import datetime
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import base64

app = Flask(__name__)

# Configuración
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'reportes')
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/api/reportes', methods=['POST'])
def recibir_reporte():
    """Recibe reporte de mantenimiento desde app web"""
    try:
        datos = request.get_json()
        
        if not datos:
            return jsonify({'error': 'No hay datos'}), 400
        
        # Validar campos requeridos
        campos_requeridos = ['repNo', 'fecha', 'responsable', 'supervisor', 'tag']
        for campo in campos_requeridos:
            if campo not in datos or not datos[campo]:
                return jsonify({'error': f'Falta campo requerido: {campo}'}), 400
        
        # Crear nombre de archivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        rep_no = secure_filename(datos['repNo'])
        filename = f"reporte_{rep_no}_{timestamp}.json"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Procesar fotos (base64 a archivos)
        fotos_guardadas = []
        if 'fotos' in datos and datos['fotos']:
            for idx, foto_b64 in enumerate(datos['fotos']):
                if foto_b64.startswith('data:image'):
                    # Extraer base64 puro
                    foto_data = foto_b64.split(',')[1]
                    foto_filename = f"reporte_{rep_no}_{timestamp}_foto{idx+1}.jpg"
                    foto_filepath = os.path.join(app.config['UPLOAD_FOLDER'], foto_filename)
                    
                    with open(foto_filepath, 'wb') as f:
                        f.write(base64.b64decode(foto_data))
                    fotos_guardadas.append(foto_filename)
        
        # Guardar datos sin firmas en base64 (reducir tamaño)
        datos_guardados = datos.copy()
        datos_guardados['fotos'] = fotos_guardadas
        
        # Guardar JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(datos_guardados, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'mensaje': 'Reporte recibido correctamente',
            'reporte_id': rep_no,
            'timestamp': timestamp,
            'archivo': filename
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reportes/<rep_no>', methods=['GET'])
def obtener_reporte(rep_no):
    """Obtiene un reporte por número"""
    try:
        rep_no = secure_filename(rep_no)
        archivos = os.listdir(app.config['UPLOAD_FOLDER'])
        
        # Buscar archivo que coincida
        for archivo in archivos:
            if archivo.startswith(f"reporte_{rep_no}_") and archivo.endswith('.json'):
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], archivo)
                with open(filepath, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                return jsonify(datos), 200
        
        return jsonify({'error': 'Reporte no encontrado'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reportes', methods=['GET'])
def listar_reportes():
    """Lista todos los reportes guardados"""
    try:
        archivos = os.listdir(app.config['UPLOAD_FOLDER'])
        reportes = []
        
        for archivo in archivos:
            if archivo.endswith('.json'):
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], archivo)
                with open(filepath, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                    reportes.append({
                        'repNo': datos.get('repNo'),
                        'fecha': datos.get('fecha'),
                        'responsable': datos.get('responsable'),
                        'tag': datos.get('tag'),
                        'archivo': archivo
                    })
        
        return jsonify({'reportes': reportes, 'total': len(reportes)}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/foto/<filename>', methods=['GET'])
def obtener_foto(filename):
    """Descarga una foto del reporte"""
    try:
        filename = secure_filename(filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Foto no encontrada'}), 404
        
        with open(filepath, 'rb') as f:
            foto_data = f.read()
        
        return foto_data, 200, {'Content-Type': 'image/jpeg'}
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check para Render"""
    return jsonify({'status': 'OK', 'timestamp': datetime.now().isoformat()}), 200


@app.route('/', methods=['GET'])
def home():
    """Página de inicio"""
    return jsonify({
        'nombre': 'Servidor Reportes Mantenimiento Roca Port MDA47',
        'version': '1.0',
        'endpoints': {
            'POST /api/reportes': 'Enviar nuevo reporte',
            'GET /api/reportes': 'Listar todos los reportes',
            'GET /api/reportes/<rep_no>': 'Obtener reporte por número',
            'GET /api/foto/<filename>': 'Descargar foto',
            'GET /health': 'Health check'
        }
    }), 200


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
