# 🚀 Guía Despliegue Render - Servidor Reportes Mantenimiento

## Paso 1: Preparar repositorio Git

### Opción A: Crear nuevo repo en GitHub
```bash
# Crear carpeta del proyecto
mkdir servidor-reportes-roca
cd servidor-reportes-roca

# Inicializar Git
git init

# Copiar los 4 archivos aquí:
# - servidor_reporte.py
# - requirements.txt
# - Procfile
# - GUIA_RENDER.md (este archivo)

# Crear .gitignore
cat > .gitignore << EOF
__pycache__/
*.py[cod]
*$py.class
*.so
.env
reportes/
venv/
.DS_Store
EOF

# Primer commit
git add .
git commit -m "Initial commit - Servidor reportes Roca Port MDA47"

# Crear repo en GitHub y hacer push
# En GitHub: New Repository > nombre "servidor-reportes-roca"
# NO inicializar con README ni .gitignore

git remote add origin https://github.com/TU_USUARIO/servidor-reportes-roca.git
git branch -M main
git push -u origin main
```

---

## Paso 2: Desplegar en Render

### 2.1 Crear cuenta y conectar GitHub
1. Ir a https://render.com
2. Sign Up con GitHub (es más fácil)
3. Autorizar Render para acceder a tus repos

### 2.2 Crear Web Service
1. Dashboard > **New +** > **Web Service**
2. Seleccionar repo `servidor-reportes-roca`
3. Llenar formulario:

| Campo | Valor |
|-------|-------|
| **Name** | `servidor-reportes-roca` |
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn servidor_reporte:app` |
| **Plan** | Free (o Starter $7/mes si necesitas almacenamiento persistente) |

### 2.3 Variables de entorno
En Settings > Environment Variables, agregar:
```
FLASK_ENV = production
PORT = 10000
UPLOAD_FOLDER = /tmp/reportes
```

⚠️ **Nota importante**: Render borra `/tmp` cuando el servicio se reinicia. Si necesitas persistencia:
- Usar plan **Starter** ($7/mes)
- O conectar S3/PostgreSQL (ver Paso 3)

### 2.4 Deploy
1. Click **Create Web Service**
2. Esperar 5-10 min mientras construye e instala
3. Cuando esté listo, aparecerá URL como:
   ```
   https://servidor-reportes-roca.onrender.com
   ```

---

## Paso 3: Guardar reportes (Opciones de almacenamiento)

### Opción A: PostgreSQL (Gratis en Render)
Si quieres guardar reportes permanentemente sin perder datos:

1. En Render > New + > PostgreSQL
2. Conectar a tu Web Service
3. Render te dará `DATABASE_URL` automáticamente
4. El servidor usará esa BD automáticamente (modificación futura)

### Opción B: AWS S3 (Recomendado)
Para subir fotos a la nube:

1. Crear cuenta AWS
2. Crear bucket S3
3. Generar Access Keys
4. Agregar a Render Environment:
   ```
   AWS_ACCESS_KEY_ID = xxx
   AWS_SECRET_ACCESS_KEY = xxx
   AWS_S3_BUCKET = tu-bucket
   AWS_REGION = us-east-1
   ```

### Opción C: Local (Render Starter Plan)
Si pagas $7/mes por Starter Plan, los reportes se guardan en:
```
/var/lib/render/reportes/
```

---

## Paso 4: Integrar con app web

En tu `reporte_mantenimiento_campo.html`, reemplazar función `guardarLocal()` para enviar al servidor:

```javascript
async function guardarEnServidor() {
    const activities = [];
    document.querySelectorAll('#activitiesTable tr').forEach((row, idx) => {
        const name = row.querySelector('.activity-name').value;
        const status = row.querySelector('.activity-status').value;
        const hh = row.querySelector('.activity-hh').value;
        if(name || status || hh) {
            activities.push({ num: idx+1, name, status, hh });
        }
    });

    const datos = {
        repNo: document.getElementById('repNo').value,
        fecha: document.getElementById('fecha').value,
        responsable: document.getElementById('responsable').value,
        supervisor: document.getElementById('supervisor').value,
        tag: document.getElementById('tag').value,
        cliente: document.getElementById('cliente').value,
        tipo: Array.from(document.querySelectorAll('input[name="tipo"]:checked')).map(x => x.value),
        disciplina: Array.from(document.querySelectorAll('input[name="disciplina"]:checked')).map(x => x.value),
        hhAsig: document.getElementById('hhAsig').value,
        hhEjec: document.getElementById('hhEjec').value,
        descripcion: document.getElementById('descripcion').value,
        activities: activities,
        aceptaQuien: document.getElementById('aceptaQuien').value,
        fotos: []
    };
    
    // Agregar fotos
    ['foto1', 'foto2', 'foto3', 'foto4'].forEach((id, idx) => {
        const preview = document.getElementById(`preview${idx+1}`);
        if (preview.style.display !== 'none') datos.fotos.push(preview.src);
    });

    try {
        const response = await fetch('https://servidor-reportes-roca.onrender.com/api/reportes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(datos)
        });
        
        const result = await response.json();
        if (result.success) {
            mostrarEstado(`✅ Reporte ${result.reporte_id} guardado en servidor`, 'success');
        } else {
            mostrarEstado(`❌ Error: ${result.error}`, 'error');
        }
    } catch (error) {
        mostrarEstado(`❌ Error de conexión: ${error.message}`, 'error');
        // Fallback a localStorage
        guardarLocal();
    }
}
```

---

## Paso 5: Verificar despliegue

### Test 1: Health Check
```bash
curl https://servidor-reportes-roca.onrender.com/health
```
Debe retornar:
```json
{"status": "OK", "timestamp": "2026-09-20T..."}
```

### Test 2: Enviar reporte de prueba
```bash
curl -X POST https://servidor-reportes-roca.onrender.com/api/reportes \
  -H "Content-Type: application/json" \
  -d '{
    "repNo": "REP-001",
    "fecha": "2026-09-20",
    "responsable": "Juan",
    "supervisor": "Carlos",
    "tag": "G-EQ-01",
    "descripcion": "Test"
  }'
```

### Test 3: Listar reportes
```bash
curl https://servidor-reportes-roca.onrender.com/api/reportes
```

---

## Endpoints API

### 📤 POST `/api/reportes`
**Enviar nuevo reporte**
```json
{
  "repNo": "REP-001",
  "fecha": "2026-09-20",
  "responsable": "Juan García",
  "supervisor": "Carlos López",
  "tag": "G-EQ-01",
  "cliente": "HLB",
  "tipo": ["Preventivo"],
  "disciplina": ["Mecánico"],
  "hhAsig": 8,
  "hhEjec": 7.5,
  "descripcion": "Cambio aceite y filtros",
  "activities": [
    {"num": 1, "name": "Cambio aceite", "status": "Completada", "hh": "2"}
  ],
  "fotos": ["data:image/jpeg;base64,..."],
  "aceptaQuien": "Supervisor HLB"
}
```

**Respuesta (201 Created):**
```json
{
  "success": true,
  "mensaje": "Reporte recibido correctamente",
  "reporte_id": "REP-001",
  "timestamp": "20260920_143025",
  "archivo": "reporte_REP-001_20260920_143025.json"
}
```

### 📋 GET `/api/reportes`
**Listar todos los reportes**
```json
{
  "reportes": [
    {
      "repNo": "REP-001",
      "fecha": "2026-09-20",
      "responsable": "Juan García",
      "tag": "G-EQ-01",
      "archivo": "reporte_REP-001_20260920_143025.json"
    }
  ],
  "total": 1
}
```

### 🔍 GET `/api/reportes/<rep_no>`
**Obtener un reporte específico**
```
GET /api/reportes/REP-001
```

### 📸 GET `/api/foto/<filename>`
**Descargar foto**
```
GET /api/foto/reporte_REP-001_20260920_143025_foto1.jpg
```

---

## Troubleshooting

### Problema: "Build failed"
**Solución**: Verificar que `requirements.txt` esté bien formato:
```bash
pip install -r requirements.txt  # Test local
```

### Problema: "503 Service Unavailable"
**Solución**: Render está iniciando. Esperar 30 segundos y reintentar. Si persiste:
1. Render Dashboard > Logs
2. Buscar errores
3. Reiniciar servicio (botón "Restart")

### Problema: "No se guardan reportes"
**Causa**: Estás en plan Free y Render reinicia cada 15 min.
**Solución**: Cambiar a Starter Plan o conectar BD PostgreSQL.

### Problema: Fotos muy pesadas / Timeout
**Solución**: Comprimir fotos antes de enviar:
```javascript
// En app web, antes de enviar
const canvas = document.createElement('canvas');
const img = new Image();
img.onload = () => {
    canvas.width = img.width * 0.7;  // Reducir resolución
    canvas.height = img.height * 0.7;
    canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height);
    // Usar canvas.toDataURL('image/jpeg', 0.7) para JPEG comprimido
};
img.src = preview.src;
```

---

## Monitoreo y logs

En Render Dashboard:
1. Seleccionar tu Web Service
2. Tab **Logs** - ver eventos en tiempo real
3. Tab **Metrics** - CPU, memoria, requests
4. Tab **Events** - historial de deploys

---

## Actualizar código

Después de hacer cambios:
```bash
git add .
git commit -m "Descripción del cambio"
git push origin main
```
Render se redeploy automáticamente 🚀

---

**¿Preguntas?** Contacta al equipo de Roca Port MDA47
