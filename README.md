# OrganizaT

OrganizaT es una aplicación backend desarrollada con **Python (FastAPI)**.

## Estructura del Proyecto

El repositorio contiene el código fuente del backend.

## Estado Actual del Backend

El backend se encuentra en desarrollo activo y cuenta con las siguientes funcionalidades principales:

1.  **Autenticación (Auth)**:
    -   Registro y Login de usuarios (JWT).
    -   Gestión de perfiles de usuario.
    -   Actualización de Avatar (URL única).

2.  **Etiquetas (Tags)**:
    -   CRUD completo de etiquetas personalizadas (nombre, color).

3.  **Tareas (Tasks)**:
    -   Creación, lectura, actualización y eliminación de tareas.
    -   Asignación de fechas límite, recordatorios y estado.
    -   **Gestión de Etiquetas en Tareas**: Asignar y desvincular múltiples etiquetas a una tarea.

## Tecnologías

- **Backend**: Python, FastAPI.
- **Despliegue Backend**: Vercel.

## Configuración y Ejecución Local

### Backend (API)

1. Crea y activa un entorno virtual (recomendado):
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. Instala las dependencias:
   ```powershell
   pip install -r requirements.txt
   ```

3. Configura la Base de Datos (Supabase):
   - Crea un proyecto en Supabase.
   - Copia el contenido de `database.txt` y ejecútalo en el editor SQL de Supabase para crear las tablas y políticas.
   - Crea un archivo `.env` en la raíz del proyecto con tus credenciales:
     ```
     SUPABASE_URL=tu_url_de_supabase
     SUPABASE_ANON_KEY=tu_anon_key_de_supabase
     SUPABASE_SERVICE_ROLE_KEY=tu_service_role_key_de_supabase # IMPORTANTE: Requerido para operaciones de escritura del backend
     ```

4. Ejecuta el servidor de desarrollo:
   ```powershell
   uvicorn main:app --reload
   ```
   - La API estará disponible en: `http://127.0.0.1:8000`
   - Documentación interactiva (Swagger): `http://127.0.0.1:8000/docs`

## Flujo de Trabajo con Git

- **Rama Principal de Desarrollo**: `development`
- **Rama de Producción**: `production` (o `main` según configuración remota)

Todos los cambios deben realizarse en la rama `development` y probarse antes de fusionarse a producción.
