# OrganizaT

OrganizaT es una aplicación móvil desarrollada con **React Native (Expo)** y un backend en **Python (FastAPI)**.

## Estructura del Proyecto

El repositorio está organizado en dos carpetas principales:

- `frontend/`: Código fuente de la aplicación móvil.
- `backend/`: API REST y lógica del servidor.

## Tecnologías

- **Frontend**: React Native, Expo.
- **Backend**: Python, FastAPI.
- **Despliegue Backend**: Vercel.

## Configuración y Ejecución Local

### Backend (API)

1. Navega a la carpeta del backend:
   ```powershell
   cd backend
   ```

2. Crea y activa un entorno virtual (recomendado):
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. Instala las dependencias:
   ```powershell
   pip install -r requirements.txt
   ```

4. Configura la Base de Datos (Supabase):
   - Crea un proyecto en Supabase.
   - Copia el contenido de `backend/database.txt` y ejecútalo en el editor SQL de Supabase para crear las tablas y políticas.
   - Crea un archivo `.env` en la carpeta `backend/` con tus credenciales:
     ```
     SUPABASE_URL=tu_url_de_supabase
     SUPABASE_ANON_KEY=tu_anon_key_de_supabase
     ```

5. Ejecuta el servidor de desarrollo:
   ```powershell
   uvicorn main:app --reload
   ```
   - La API estará disponible en: `http://127.0.0.1:8000`
   - Documentación interactiva (Swagger): `http://127.0.0.1:8000/docs`

### Frontend (App Móvil)

1. Navega a la carpeta del frontend:
   ```powershell
   cd frontend
   ```

2. Instala las dependencias:
   ```powershell
   npm install
   ```

3. Inicia el servidor de Expo:
   ```powershell
   npx expo start
   ```
   - Escanea el código QR generado con la app **Expo Go** en tu dispositivo móvil.
   - O presiona `a` para abrir en un emulador de Android (si está configurado).

## Flujo de Trabajo con Git

- **Rama Principal de Desarrollo**: `development`
- **Rama de Producción**: `production` (o `main` según configuración remota)

Todos los cambios deben realizarse en la rama `development` y probarse antes de fusionarse a producción.
