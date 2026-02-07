---
alwaysApply: true
---
# Flujo de Desarrollo y Comandos

## Configuración de Entorno
- **Sistema Operativo:** Windows (prioridad) / macOS (compatible).
- **Shell:** PowerShell (Win) / zsh (Mac).
- **Python:** 3.10+ (usar `python -m venv venv`).
- **Node:** LTS.

## Comandos Comunes

### Backend (`/backend`)
**Windows (PowerShell):**
```powershell
# Setup Inicial
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Ejecución Desarrollo
uvicorn main:app --reload
# API: http://127.0.0.1:8000
# Docs: http://127.0.0.1:8000/docs
```

**macOS/Linux (Bash/Zsh):**
```bash
# Setup Inicial
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Ejecución Desarrollo
python -m uvicorn main:app --reload
```

### Frontend (`/frontend`)
```powershell
# Setup
npm install

# Ejecución
npm start  # o npx expo start
npm run android
npm run web
```

## Git Workflow
- **Ramas:**
  - `development`: Rama principal de desarrollo. Todos los cambios van aquí primero.
  - `production` (o `main`): Rama estable para despliegue.
- **Commits:**
  - Incluir co-autoría para cambios de IA: `Co-Authored-By: Trae <trae@trae.ai>`
  - Mensajes claros y descriptivos.

## Gestión de Cambios y Reglas
- **Documentos Vivos:** Las reglas en `.trae/rules/` deben actualizarse al identificar nuevos patrones o decisiones técnicas importantes durante la sesión.
- **Actualización:** Al final de la sesión o cuando se solicite explícitamente, revisar y actualizar estos documentos.

## Verificación y Testing
- **Backend:**
  - Usar `curl` para probar endpoints rápidamente antes de integrar con frontend.
  - Verificar códigos de estado HTTP (201 Created, 400 Bad Request, 401 Unauthorized, 409 Conflict).
  - Validar estructuras JSON de respuesta.
- **Validación Automatizada (Requerida):**
  - Ejecutar script de integración: `python test_api_full.py`
  - Revisar logs generados: `api_test_log.json` para confirmar payloads y respuestas correctas.
  - El script debe cubrir el flujo completo: Crear -> Vincular -> Leer (Verificar Links) -> Borrar.
- **Validación de Cambios:** Antes de dar una tarea por terminada, verificar "camino feliz" y casos de error comunes.

## Despliegue
- **Backend:** Vercel (`vercel.json`).
- **Frontend:** Expo / Stores.
