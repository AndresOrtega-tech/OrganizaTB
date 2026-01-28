---
alwaysApply: false
description: Cuando vyaamos a modificar la estructura de las carpetas, o un cambio en el programa que sea grande
---
# Flujo de Desarrollo y Comandos

## Configuración de Entorno
- **Sistema Operativo:** Windows (prioridad).
- **Shell:** PowerShell.
- **Python:** 3.10+ (usar `python -m venv venv`).
- **Node:** LTS.

## Comandos Comunes

### Backend (`/backend`)
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

## Despliegue
- **Backend:** Vercel (`vercel.json`).
- **Frontend:** Expo / Stores.
