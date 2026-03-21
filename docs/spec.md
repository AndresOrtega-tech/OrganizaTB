# SPEC — OrganizaT API
<!-- inferido del código -->

Última actualización: <!-- confirmado por Andres -->  
Autor: Pipeline Initializer (generado automáticamente)

Resumen
-------
Este documento especifica los endpoints principales, modelos (schemas) y user stories implementadas por el backend de OrganizaT. El objetivo es dejar una especificación compacta y fiel al código actual para referencia del equipo de producto y desarrollo.

Notas generales
- Base técnica: FastAPI + supabase-py (cliente Supabase) <!-- inferido del código -->
- Autenticación: Supabase Auth (JWT). Endpoints protegidos requieren `Authorization: Bearer <token>` (cabecera HTTP). <!-- inferido del código -->
- Rate limiting: SlowAPI está integrado (Limiter con key = get_remote_address). <!-- inferido del código -->
- RLS (Row Level Security) en Supabase: <!-- confirmado por Andres --> actualmente DESACTIVADO (en desarrollo). <!-- confirmado por Andres -->
- Deploy: Vercel (archivo `vercel.json` apunta a `main.py`). <!-- inferido del código -->

User Stories (inferred -> historias de usuario)
-----------------------------------------------
- US-001 — Autenticación y Perfil
  - Como usuario, quiero registrarme con email y contraseña, iniciar sesión y renovar mis tokens para usar la app.
  - Como usuario autenticado, quiero ver y actualizar mi perfil (avatar, contraseña).
  - Endpoints: registro, login, refresh, /me, avatar, password change/reset.

- US-002 — Gestión de Tags
  - Como usuario, quiero crear, listar, editar y eliminar mis etiquetas (tags) para organizarlas por color/nombre.

- US-003 — Gestión de Tareas (Tasks)
  - Como usuario, quiero crear tareas con título, descripción, fecha límite, prioridad y recordatorios.
  - Como usuario, quiero listar mis tareas con modos `home` y `tasks` (paginación por cursor), filtrar por tags y prioridad.
  - Como usuario, quiero actualizar, obtener y eliminar tareas.
  - Como usuario, quiero vincular tags y ver relaciones (tags, notas, eventos) de una tarea.

- US-004 — Gestión de Notas (Notes)
  - Como usuario, quiero crear, listar, actualizar, archivar y eliminar notas.
  - Como usuario, quiero asignar tags y ver relaciones (tags, tareas, eventos).
  - Soporte para campo `summary` (para IA/automatizaciones en el futuro).

- US-005 — Gestión de Eventos (Events)
  - Como usuario, quiero crear eventos con start/end, location, all-day flag, y recordatorios.
  - Como usuario, quiero listar eventos por rango de fechas y ver relaciones y tags.
  - (Events refactorizado y finalizado) <!-- confirmado por Andres -->

- US-006 — Recordatorios (Reminders)
  - Como sistema, debo generar recordatorios al crear/actualizar tareas y eventos.
  - Como usuario, quiero listar, actualizar y eliminar recordatorios.
  - Worker para enviar notificaciones está en el plan pero no implementado. <!-- confirmado por Andres -->

- US-007 — Relaciones (Relations)
  - Como usuario, quiero vincular/desvincular tareas ↔ notas, tareas ↔ eventos, notas ↔ eventos via endpoints dedicados.

API: Endpoints por módulo
-------------------------

Nota: Para cada endpoint se indica método, ruta, resumen y (cuando aplica) modelos de request/response (nombres Pydantic detectados en `*/schemas.py`).  
Los modelos completos están listados en la sección "Modelos".

A. Health
- GET `/`  
  - Resumen: Mensaje de bienvenida.
  - Response: { "message": "Hola Mundo desde FastAPI en Vercel" } <!-- inferido del código -->

- GET `/health`  
  - Resumen: Estado básico incluyendo conexión a Supabase.
  - Response: { "status": "ok"|"error", "supabase_connected": bool, "supabase_url": string|null }

- GET `/tables`  
  - Resumen: Llama a RPC `get_tables` en Supabase (requiere función RPC creada en la BD).  
  - Response: { "tables": [...] } o error con instrucciones para crear la función RPC. <!-- inferido del código -->

B. Auth / Users
- POST `/api/users/`  
  - Resumen: Registrar nuevo usuario (crea en Supabase Auth y upsert en `profiles`).  
  - Request: `UserCreate`  
  - Response: mensaje y datos básicos del usuario.  
  - Notas: verifica unicidad de email y unicidad global del avatar (si provisto). <!-- inferido del código -->

- POST `/api/auth/login`  
  - Resumen: Login con email+password. Devuelve `access_token`, `refresh_token`, `expires_in` y `user` (email, full_name, avatar).  
  - Request: `UserLogin`  
  - Response: `Token` model. <!-- inferido del código -->

- POST `/api/auth/refresh`  
  - Resumen: Renovación de tokens a partir de `refresh_token`.  
  - Request: `RefreshTokenRequest`  
  - Response: `Token`

- GET `/api/users/me`  
  - Resumen: Obtiene información del usuario autenticado (`CurrentUser`).  
  - Response: `CurrentUser`

- PATCH `/api/users/avatar`  
  - Resumen: Actualiza avatar (nombre único).  
  - Request: `UserAvatarUpdate`  
  - Response: { message, avatar }

- PATCH `/api/users/password`  
  - Resumen: Cambia contraseña del usuario autenticado (usa token bearer para autenticar).  
  - Request: `UserPasswordUpdate`  
  - Response: { message } (realiza petición a Supabase Auth API internamente).

- POST `/api/users/password/reset`  
  - Resumen: Solicita email de reset (reset_password_email de Supabase).  
  - Request: `UserPasswordResetRequest`  
  - Response: { message }

C. Tags
- POST `/api/tags/`  
  - Request: `TagCreate`  
  - Response: `TagResponse`  
  - Reglas: nombre único por usuario (UNIQUE(user_id, name) en BD). icon se guarda como null por ahora en creación. <!-- inferido del código -->

- GET `/api/tags/`  
  - Response: List[`TagResponse`]

- PATCH `/api/tags/{tag_id}`  
  - Request: `TagUpdate` (nota: `icon` pendiente en TagUpdate en código—ver TODO) <!-- TODO: verificar -->  
  - Response: `TagResponse`

- DELETE `/api/tags/{tag_id}`  
  - Response: 204, cascade en tablas de unión.

D. Tasks
- POST `/api/tasks/`  
  - Request: `TaskCreate` (incluye `reminders: List[ReminderConfig]`)  
  - Response: `TaskCreateResponse` (incluye `reminders_data` generados y `calendar_event_id` igual a `id`)  
  - Reglas: si se envían reminders y due_date se crean registros en `reminders`.

- GET `/api/tasks/`  
  - Query params:
    - `view`: `home` | `tasks` (pattern enforced)  
    - `tab`: `pending` | `completed` (en `view=tasks`)  
    - `tag_ids`: array (filtro AND: la tarea debe incluir todas las tags)  
    - `priority`: `baja`|`media`|`alta`  
    - `end_date`: datetime  
    - `limit`: int (1..50), default 10  
    - `cursor`: ISO datetime (cursor por due_date)
  - Response: `PaginatedTaskResponse` = { data: List[TaskResponse], next_cursor, has_more }
  - Reglas de negocio: `view=home` muestra ventana hoy→hoy+7 (overdue pending, pending in window, completed in window). Orden y paginación tal como implementado en `tasks/api.py`. <!-- inferido del código -->

- GET `/api/tasks/{task_id}`  
  - Response: `TaskResponse` (incluye `reminders_data`, no incluye tags directamente; usar `/related` para relaciones completas).

- GET `/api/tasks/{task_id}/related`  
  - Response: `TaskRelatedResponse` { tags, notes, events }

- PATCH `/api/tasks/{task_id}`  
  - Request: `TaskUpdate` (si `reminders` presente reemplaza completamente los reminders anteriores).  
  - Response: `TaskResponse`

- DELETE `/api/tasks/{task_id}`  
  - Response: 204

- POST `/api/tasks/{task_id}/tags`  
  - Request: `TaskAssignTags` { tag_id }  
  - Response: { message, assigned }

- DELETE `/api/tasks/{task_id}/tags/{tag_id}`  
  - Response: 204

E. Notes
- POST `/api/notes/`  
  - Request: `NoteCreate`  
  - Response: `NoteResponse`

- GET `/api/notes/`  
  - Query params: `is_archived` (default false), `tag_ids` (AND), `sort_by=updated_at`, `order=asc|desc`, `limit`
  - Response: List[`NoteResponse`]

- GET `/api/notes/{note_id}`  
  - Response: `NoteResponse`

- PATCH `/api/notes/{note_id}`  
  - Request: `NoteUpdate` (usa `model_dump`/exclude_unset en implementación)  
  - Response: `NoteResponse`

- PATCH `/api/notes/{note_id}/summary`  
  - Request: `NoteSummaryUpdate` — actualiza únicamente el campo `summary` (acepta null).  
  - Response: `NoteResponse`

- DELETE `/api/notes/{note_id}`  
  - Response: 204

- POST `/api/notes/{note_id}/tags`  
  - Request: `NoteAssignTag` { tag_id }  
  - Response: { message, assigned }

- DELETE `/api/notes/{note_id}/tags/{tag_id}`  
  - Response: 204

- GET `/api/notes/{note_id}/related`  
  - Response: `NoteRelatedResponse` { tags, tasks, events }

F. Events
- POST `/api/events/`  
  - Request: `EventCreate` (incluye `reminders`)  
  - Response: `EventResponse` (incluye `reminders_data`)

- GET `/api/events/`  
  - Query params: `start_date`, `end_date`, `tag_ids`  
  - Response: List[`EventResponse`]

- GET `/api/events/{event_id}`  
  - Response: `EventResponse`

- PATCH `/api/events/{event_id}`  
  - Request: `EventUpdate` (si `reminders` presente, reemplaza reminders existentes)  
  - Response: `EventResponse` (incluye tags y reminders_data)

- DELETE `/api/events/{event_id}`  
  - Response: 204

- GET `/api/events/{event_id}/related`  
  - Response: `EventRelatedResponse` { tags, tasks, notes }

- POST `/api/events/{event_id}/tags`  
  - Request: `EventAssignTag` { tag_id }  
  - Response: { message, assigned }

- DELETE `/api/events/{event_id}/tags/{tag_id}`  
  - Response: 204

(G) Reminders
- GET `/api/reminders/`  
  - Query params: `status`, `start_date`, `end_date`  
  - Response: List[`ReminderResponse`] (aplana `task_title` y `event_title` si están presentes)

- PATCH `/api/reminders/{reminder_id}`  
  - Request: `ReminderUpdate` (remind_at, status)  
  - Response: `ReminderResponse`

- DELETE `/api/reminders/{reminder_id}`  
  - Response: 204

H. Relations
- POST `/api/relations/task-note` — vincular tarea y nota  
  - Request: `TaskNoteLink`  
  - Response: { message }

- DELETE `/api/relations/task-note` — desvincular tarea y nota  
  - Request: `TaskNoteLink`  
  - Response: { message }

- POST `/api/relations/task-event` — vincular tarea y evento  
  - Request: `TaskEventLink`  
  - Response: { message }

- DELETE `/api/relations/task-event` — desvincular tarea y evento  
  - Request: `TaskEventLink`  
  - Response: { message }

- POST `/api/relations/note-event` — vincular nota y evento  
  - Request: `NoteEventLink`  
  - Response: { message }

- DELETE `/api/relations/note-event` — desvincular nota y evento  
  - Request: `NoteEventLink`  
  - Response: { message }

Modelos (Schemas principales)
-----------------------------

A continuación se listan los modelos Pydantic detectados en `*/schemas.py`. Marqué los campos principales y las restricciones notables.

1) Auth / Users
- `UserCreate`
  - `email: EmailStr`
  - `password: str (min_length=6)`
  - `full_name?: str`
  - `avatar?: str` <!-- avatar es nombre único, no URL --> <!-- inferido del código -->

- `UserLogin`
  - `email`, `password`

- `Token`
  - `access_token: str`, `token_type: str = "bearer"`, `refresh_token?: str`, `expires_in?: int`, `user: dict`

- `CurrentUser`
  - `email: EmailStr`, `full_name?: str`, `avatar?: str`

2) Tags
- `TagCreate` / `TagBase`
  - `name: str (1..50)`, `color: str (hex)`, `icon?: str` (icon en creación no requerido)
- `TagUpdate`
  - `name?: str`, `color?: str`, `icon?: str` (en código icon en TagUpdate pendiente) <!-- TODO: verificar -->
- `TagResponse`
  - `id: str`, `user_id: str`, `name`, `color`, `icon`, `created_at`

3) Tasks
- `TaskBase`
  - `title: str`, `description?: str (<=500)`, `due_date?: datetime`, `is_completed: bool`, `priority: "baja"|"media"|"alta"`
- `TaskCreate(TaskBase)`
  - `reminders?: List[ReminderConfig]`
- `TaskUpdate`
  - Campos opcionales: title, description, due_date, is_completed, priority, reminders
- `TaskCreateResponse` / `TaskResponse`
  - `id`, `user_id`, `calendar_event_id?`, `media_url?`, `created_at`, `updated_at`, `reminders_data: List[ReminderResponse]`, `has_reminder: bool`, `tags: List[TagSummary]` (TaskResponse)

4) Notes
- `NoteBase`: `title?`, `content? (<=800)`, `summary? (<=500)`, `is_archived: bool`
- `NoteCreate`, `NoteUpdate`
- `NoteResponse`: incluye `id`, `user_id`, `media_url?`, `created_at`, `updated_at`, `tags: List[TagSummary]`

5) Events
- `EventBase`: `title`, `description? (<=500)`, `start_time`, `end_time`, `location?`, `is_all_day: bool`
- `EventCreate` includes `reminders?: List[ReminderConfig]`
- `EventResponse`: `id`, `user_id`, timestamps, `reminders_data`, `has_reminder`, `tags: List[TagSummary]`

6) Reminders
- `ReminderConfig`: `{ value: int (>0), unit: "minutes"|"hours"|"days" }`
- `ReminderBase`: `remind_at: datetime`, `status: str = "pending"`
- `ReminderResponse`: `id`, `user_id`, `task_id?`, `event_id?`, `created_at`, and optional `task_title` / `event_title`

7) Auxiliares
- `TagSummary`: `id`, `name`, `color?`, `icon?`
- `TaskNoteLink`, `TaskEventLink`, `NoteEventLink` — payloads simples con IDs

Variables de entorno relevantes
-------------------------------
- `SUPABASE_URL` — URL del proyecto Supabase. <!-- inferido del README y database.py -->
- `SUPABASE_SERVICE_ROLE_KEY` (o `SERVICE_ROLE` o `SUPABASE_ANON_KEY`) — clave usada por el backend (service role preferida). <!-- inferido del código -->
- (Otros variables de entorno pueden existir para Vercel) <!-- TODO: verificar -->

Integraciones externas
---------------------
- Supabase Auth & PostgreSQL (DB) — cliente `supabase-py` usado por el backend (queries, auth, RPC). <!-- inferido del código -->
- Vercel — despliegue mediante `@vercel/python` con `main.py` como entrypoint. <!-- inferido del código -->

Errores y formatos de respuesta
------------------------------
- Uso general de HTTPException en FastAPI para errores: 400 para errores generales, 401 para auth, 404 para no encontrado, 409 para conflicto, 500 para errores del servidor.
- many endpoints retornan `{ "message": "...", ... }` en operaciones no-CRUD o confirmatorias.

Consideraciones operacionales y TODOs
------------------------------------
- TODO-001: Worker/Servicio de notificaciones para procesar reminders (cambiar status a `sent`/`failed`) — está en el roadmap pero no implementado. <!-- confirmado por Andres -->
- TODO-002: Activar RLS y validar políticas acorde al modelo `auth.uid()` — RLS actualmente desactivado en dev. <!-- confirmado por Andres -->
- TODO-003: Añadir `icon` a `TagUpdate` schema para permitir edición del icon (campo `icon` existe en BD). <!-- inferido del código -->
- TODO-004: Documentar y publicar `improvement_insights` API si se decide implementar (tabla ya existe). <!-- confirmado por Andres: fuera de foco por ahora -->
- TODO-005: Validar que no exista ningún cambio funcional pendiente antes de hacer merge (documentación ya separada en `docs/` por la rama `development`). <!-- confirmado por Andres -->

Referencias en el código
------------------------
- Routers principales: `main.py` incluye routers de `auth`, `tags`, `tasks`, `notes`, `events`, `reminders`, `relations`. <!-- inferido del código -->
- DB client: `database.py` crea `supabase` client usando variables de entorno. <!-- inferido del código -->
- Reglas y especificaciones por módulo en `*/rules.md` (ya existentes). <!-- inferido del repo -->

Cambios confirmados desde el equipo
-----------------------------------
- `events` está finalizado y refactorizado; los `rules.md` anteriores pueden estar desactualizados. <!-- confirmado por Andres -->
- RLS está desactivado durante el desarrollo. <!-- confirmado por Andres -->
- Worker de reminders está en plan, no implementado. <!-- confirmado por Andres -->
- `improvement_insights` no será foco inmediato. <!-- confirmado por Andres -->

Fin del documento
-----------------
<!-- inferido del código -->