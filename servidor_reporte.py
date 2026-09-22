@app.route('/api/upload-pdf', methods=['POST', 'OPTIONS'])
def upload_pdf():
    """Recibe PDF en base64 y lo sube a Drive"""
    if request.method == 'OPTIONS':
        return '', 204
    
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
        
        # ⭐ AQUÍ SE APLICÓ EL CAMBIO PARA EVITAR EL ERROR DE CUOTA (storageQuotaExceeded)
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink',
            supportsAllDrives=True
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
