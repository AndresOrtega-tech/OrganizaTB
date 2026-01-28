# Reglas de Backend (FastAPI + Supabase)

## Stack Tecnológico
- **Lenguaje:** Python (3.10+ con soporte para `|` operator).
- **Framework:** FastAPI (Async).
- **Base de Datos:** Supabase (PostgreSQL).
- **ORM/Driver:** `supabase-py` client, `psycopg2-binary`.
- **Validación:** Pydantic.
- **Rate Limiting:** SlowAPI.

## Arquitectura y Estructura
- **Modularidad:** El código debe ser modular. Cada funcionalidad principal (Auth, Tags, Tasks) debe tener su propio paquete con `api.py` (endpoints) y `schemas.py` (modelos).
- **Límite de Carpetas:** Evitar anidación profunda. Máximo 3 niveles de carpetas para proyectos simples.
- **Entry Point:** `main.py` registra todos los routers y configura middlewares (CORS, Rate Limit).

### Estructura de Directorios Actual
```
backend/
├── auth/           # Módulo de Autenticación
│   ├── api.py
│   ├── dependencies.py
│   └── schemas.py
├── tags/           # Módulo de Etiquetas
├── tasks/          # Módulo de Tareas
├── database.py     # Cliente Supabase
└── main.py         # App Entry Point
```

## Base de Datos (Supabase)
- **Seguridad (RLS):** Row Level Security habilitado en todas las tablas.
- **Claves:** 
  - `SUPABASE_SERVICE_ROLE_KEY`: Usar para operaciones backend/admin (bypassea RLS).
  - `SUPABASE_ANON_KEY`: Usar para cliente (respetar RLS).
- **Schema:** Definido en `database.txt` (referencia). Tablas principales: `profiles`, `tags`, `tasks`, `notes`, `improvement_insights`.
- **Relaciones:** Usar UUIDs para IDs. Claves foráneas con `ON DELETE CASCADE`.

## Convenciones de Código
- **Estilo:** Snake_case para funciones y variables.
- **Documentación:** Comentarios claros en funciones complejas y endpoints.
- **Importaciones:** Usar bloque `try/except` para soportar tanto ejecución local como despliegue en Vercel (importaciones absolutas vs relativas).
  ```python
  try:
      from backend.database import supabase
  except ImportError:
      from database import supabase
  ```
- **Manejo de Errores:** Retornar códigos HTTP adecuados y mensajes descriptivos en español.

## Endpoints y APIs
- **Autenticación:** Tokens JWT (Bearer) en headers.
- **Rutas:** Prefijo `/api` para todos los endpoints.
- **Variables de Entorno:** NUNCA hardcodear credenciales. Usar `os.getenv` o `python-dotenv`.
