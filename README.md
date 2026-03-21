# OrganizaT

OrganizaT es el backend de una aplicación de productividad personal orientada a gestionar tareas, notas, eventos, recordatorios y relaciones entre entidades usando FastAPI y Supabase.

## Inicio Rápido

### Prerrequisitos

- Python 3.x
- Un proyecto de Supabase
- Entorno virtual local (`venv`)

### Instalación

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuración de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
SUPABASE_URL=tu_url_de_supabase
SUPABASE_SERVICE_ROLE_KEY=tu_service_role_key
SUPABASE_ANON_KEY=tu_anon_key_opcional
```

### Base de datos

- Ejecuta `database.txt` en el SQL Editor de Supabase para crear tablas, relaciones y políticas base.
- El estado actual de RLS debe considerarse **pendiente de reactivar** y no se planea activarlo en el corto plazo.

### Ejecución local

```bash
uvicorn main:app --reload
```

- API local: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`

## Variables de Entorno

| Variable | Descripción | Requerida |
|---|---|---|
| `SUPABASE_URL` | URL del proyecto Supabase | Sí |
| `SUPABASE_SERVICE_ROLE_KEY` | Clave principal del backend | Sí |
| `SUPABASE_ANON_KEY` | Fallback opcional | No |

Para el detalle completo, revisa `docs/SPECS.md`.

## Scripts Disponibles

| Script / comando | Descripción |
|---|---|
| `uvicorn main:app --reload` | Ejecuta la API en desarrollo |
| `pip install -r requirements.txt` | Instala dependencias |

## Estructura del Proyecto

```text
OrganizaT/
├── auth/
├── events/
├── notes/
├── relations/
├── reminders/
├── tags/
├── tasks/
├── docs/
├── database.py
├── database.txt
├── main.py
├── requirements.txt
└── vercel.json
```

Para una vista más detallada, revisa `docs/ARCHITECTURE.md`.

## Tecnologías

- Python
- FastAPI
- Supabase
- PostgreSQL
- SlowAPI
- Vercel
- python-dotenv

## Documentación

| Archivo | Descripción |
|---|---|
| `docs/SPECS.md` | Stack, endpoints, modelos, variables e integraciones |
| `docs/ARCHITECTURE.md` | Arquitectura, diagramas, estructura y ADR inicial |
| `docs/CHANGELOG.md` | Línea base funcional y cambios relevantes |

## Estado funcional actual

- Auth con login, registro, refresh y recuperación de contraseña
- CRUD de tags por usuario
- CRUD de tareas con filtros, cursor, recordatorios y tags
- CRUD de notas con archivado, resumen y tags
- CRUD de eventos con tags, recordatorios y relaciones
- CRUD parcial de recordatorios
- Relaciones cruzadas entre tareas, notas y eventos

## Flujo de Trabajo con IA

- Usa `/init-docs` una sola vez para generar la documentación inicial del proyecto.
- Usa `/update-docs` al final de cada sesión para mantener `README.md` y `docs/` sincronizados.

## Flujo de Trabajo con Git

- Rama de desarrollo: `development`
- Rama estable / producción: `production`

Los cambios deben realizarse en `development` y validarse antes de promoverse.
