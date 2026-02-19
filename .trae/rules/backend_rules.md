---
alwaysApply: true
---
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
│   ├── api.py      # Endpoints HTTP
│   ├── service.py  # Lógica de Negocio (Reutilizable)
│   └── schemas.py
├── notes/          # Módulo de Notas
├── events/         # Módulo de Eventos (Calendario)
├── reminders/      # Módulo de Recordatorios
├── mcp/            # Módulo Model Context Protocol (AI)
│   ├── server.py   # Definición de Tools
│   └── main.py     # Entry point MCP
├── database.py     # Cliente Supabase
└── main.py         # App Entry Point
```

## Patrones de Arquitectura

### 1. Service Layer Pattern (Capa de Servicio)
Para permitir que tanto la API REST (App Móvil) como el Agente IA (MCP) compartan la misma lógica de negocio, se debe separar la lógica de los endpoints.
- **`api.py` (Controller):** Solo maneja HTTP (Request/Response), validación de entrada, extracción de usuario (Auth) y manejo de errores HTTP. Llama a funciones de `service.py`.
- **`service.py` (Business Logic):** Contiene la lógica pura. Recibe datos limpios (ids, pydantic models), interactúa con la BD (Supabase) y retorna objetos de dominio. NO depende de `FastAPI.Request` ni lanza `HTTPException` (usa excepciones nativas o retorna `None`).
- **`mcp/server.py` (AI Interface):** Expone las funciones de `service.py` como "Herramientas" para la IA.

### 2. Integración IA & Memoria (Chat)
- **Persistencia:** El historial de chat se guarda en Supabase para mantener contexto (Short-term memory).
  - Tabla `chat_sessions`: Agrupa conversaciones.
  - Tabla `chat_messages`: Guarda mensajes (user/assistant) y metadata de herramientas ejecutadas.
- **Flujo:** Frontend -> API Chat -> LLM -> Service Layer -> DB.

### 3. Optimización de Consultas (Supabase Joins)
Para evitar el problema N+1 y múltiples llamadas a la API de Supabase, utilizar la sintaxis de Joins en las consultas `select`.
- **Patrón:** `select("*, linked_table(column1, column2)")`
- **Uso:** Al obtener una Tarea, traer sus Notas y Eventos en la misma consulta.
  ```python
  response = supabase.table("tasks").select(
      "*, task_notes(notes(id, title)), event_tasks(events(id, title))"
  ).eq("id", task_id).single().execute()
  ```
- **Procesamiento:** El resultado anidado debe procesarse en Python para aplanar la estructura antes de pasarla al modelo Pydantic (eliminar tablas intermedias como `task_notes`).

### 4. Modelos de Resumen (Pydantic Summary Models)
Para evitar errores de referencia circular (RecursionError) y sobrecarga de datos:
- **Regla:** No incluir el modelo completo de una entidad vinculada dentro de otra.
- **Solución:** Crear modelos `Summary` (ej. `TaskSummary`, `NoteSummary`) que solo incluyan los campos esenciales (`id`, `title`, `is_completed`).
- **Ejemplo:** `TaskResponse` contiene una lista de `NoteSummary`, no de `NoteResponse`.

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

## Patrones de Implementación Específicos

### 1. Mapeo API ↔ DB (Campos Discrepantes)
Si el API expone un campo con nombre diferente al de la BD (ej. `avatar` vs `avatar_url`):
- **Lectura:** Consultar el campo de BD (`avatar_url`) y asignarlo manualmente a la variable del modelo de respuesta (`avatar`).
- **Escritura:** Recibir el campo del modelo (`avatar`) e insertarlo en la columna correcta de BD (`avatar_url`).
- **Validación:** Si se requiere unicidad, consultar la columna de BD antes de insertar.

### 2. Manejo de Errores Supabase (Auth)
- **Versiones Recientes:** `supabase.auth.sign_up` y similares lanzan excepciones (`AuthApiError`) en lugar de devolver un objeto con atributo `.error`.
- **Patrón:** Usar bloques `try-except` para capturar fallos en autenticación. Validar éxito verificando si `response.user` no es nulo.

### 3. Creación de Perfiles de Usuario (Triggers)
- **Automatización:** La creación de registros en la tabla `profiles` debe ser manejada automáticamente por un **Trigger** de PostgreSQL (`on_auth_user_created`) al insertar en `auth.users`.
- **Evitar Upserts Manuales:** No realizar inserciones manuales en `profiles` desde el endpoint de registro para evitar condiciones de carrera o errores de llaves foráneas. Pasar datos adicionales (metadata) en `options.data` de `sign_up`.

### 4. Filtrado Avanzado (Tags y Relaciones)
- **Lógica AND en Relaciones M2M:**
  - Supabase `in_` funciona como OR.
  - Para filtrar elementos que tengan **TODOS** los tags (AND):
    1. Usar `!inner` en la query para filtrar candidatos (OR).
    2. Realizar el filtrado estricto (AND) en memoria (Python) verificando `required_tags.issubset(found_tags)`.
- **Deprecaciones:** Usar `pattern` en lugar de `regex` en `Query` de FastAPI.

### 5. Filtrado por Vista (`view` param)
Para endpoints que sirven a múltiples vistas del frontend con necesidades distintas, usar un param `view` en lugar de duplicar endpoints.
- **Retrocompatible:** si no se envía `view`, el comportamiento es el clásico con filtros manuales.
- **`view` sobreescribe filtros implícitos:** cuando se usa `view`, parámetros como `is_completed` se ignoran (view los aplica automáticamente).
- **Uso de `datetime.now(timezone.utc)`** para calcular rangos de fecha (no usar `datetime.utcnow()`, está deprecado).

### 6. Paginación por Cursor
Para endpoints con grandes volúmenes de datos, usar cursor pagination basado en el campo de ordenamiento principal (generalmente `due_date`).
- **Patrón:**
  1. El cliente envía `cursor` (valor ISO 8601 del último item recibido) y `limit`.
  2. El backend filtra `campo > cursor` y solicita `limit + 1` registros.
  3. Si `len(results) > limit` → `has_more = True`, recortar a `limit` items.
  4. `next_cursor` = `due_date` del último item cuando `has_more = True` (null si no hay más o si el item no tiene due_date).
- **Sort obligatorio:** cuando se usa cursor o `view`, forzar `ORDER BY due_date ASC` para consistencia.
- **Nulls:** en Postgres, `ORDER BY due_date ASC` pone NULLs al final por defecto — no necesita configuración extra.
- **Response model:** usar `PaginatedResponse` con forma `{ data, next_cursor, has_more }`.

### 7. Índices Compuestos (Supabase)
- Guardar las migraciones SQL en `migrations/` con nombre `NNN_descripcion.sql`.
- Crear índices compuestos para columnas que se combinan frecuentemente en queries: `(user_id, is_completed, due_date)`.
- Usar `CREATE INDEX IF NOT EXISTS` para idempotencia.
