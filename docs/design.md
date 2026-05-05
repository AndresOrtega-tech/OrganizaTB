# Design — OrganizaT API
<!-- inferido del código -->

Última actualización: 2026-03-21

Resumen
-------
Documento de diseño técnico que describe la arquitectura real encontrada en el código, los componentes principales, flujos de datos y decisiones relevantes para la operación y evolución del backend OrganizaT.

Elementos marcados:
- <!-- inferido del código --> lo que deduje del código.
- <!-- confirmado por Andres --> lo que el maintainer confirmó en la conversación.
- <!-- TODO: verificar --> puntos que requieren confirmación manual (RLS, procesos externos, etc.).

Arquitectura general
--------------------
Arquitectura: Monolito backend en Python ejecutándose como una aplicación FastAPI, con Supabase (Postgres + Auth) como backend de persistencia y auth. Deploy objetivo: Vercel usando `@vercel/python` y `main.py` como entrypoint.
<!-- inferido del código -->

Arquitectura (vista simplificada)
--------------------------------
API Client (Frontend web/mobile)
        │
        ▼
  FastAPI app (main.py)
  ├─ Rate limiting (slowapi)
  ├─ CORS middleware
  ├─ Routers:
  │   ├─ /api/auth   -> auth/api.py
  │   ├─ /api/users  -> users routes (auth module)
  │   ├─ /api/tags   -> tags/api.py
  │   ├─ /api/tasks  -> tasks/api.py
  │   ├─ /api/notes  -> notes/api.py
  │   ├─ /api/events -> events/api.py
  │   ├─ /api/reminders -> reminders/api.py
  │   └─ /api/relations -> relations/api.py
  └─ Database client (supabase-py)
        │
        ▼
  Supabase (Postgres + Auth) — tablas públicas + auth.users + triggers
  - tablas: profiles, tags, tasks, notes, events, reminders, task_tags, note_tags, event_tags, task_notes, event_tasks, event_notes, improvement_insights
  <!-- inferido del código -->

Componentes principales
-----------------------

1. Entrada / Orquestación
   - `main.py` — instancia de FastAPI, configuración CORS, rate limiter (SlowAPI), inclusión de routers y endpoints de salud (`/`, `/health`, `/tables`).
   <!-- inferido del código -->

2. Auth
   - `auth/api.py`, `auth/schemas.py`, `auth/dependencies.py`
   - Delegación de autenticación a Supabase Auth (sign_up, sign_in_with_password, refresh_session, get_user).
   - `get_current_user` valida tokens con `supabase.auth.get_user(token)`.
   - Endpoints: register, login, refresh, /me, update avatar, change password, request password reset.
   <!-- inferido del código -->

3. Módulos de dominio (cada uno con routers + schemas)
   - `tags/` — CRUD de etiquetas (unique per user), validación de color hex.
   - `tasks/` — CRUD de tareas, paginación por cursor, vistas `home` y `tasks` (tabs), asignación de tags, generación de reminders.
   - `notes/` — CRUD de notas, archivado, campo `summary`, asignación de tags.
   - `events/` — CRUD de eventos (start/end, reminders), tags y relaciones. Código actualizado/refactorizado a patrón estandar.
   - `reminders/` — Listado y gestión de recordatorios (PATCH/DELETE). Los reminders se crean desde tasks/events.
   - `relations/` — Endpoints para vincular/desvincular task↔note, task↔event, note↔event.
   <!-- inferido del código -->

4. Persistencia y SQL
   - Cliente: `database.py` crea `supabase` client usando `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` (o alias).
   - Scripts: `database.txt` y migraciones en `supabase/migrations/`.
   - Constraints y triggers: hay triggers para crear/actualizar `profiles` al registrarse; varias migraciones que agregan `priority`, `summary`, tablas de eventos/recordatorios, etc.
   <!-- inferido del código -->

5. Observabilidad y seguridad
   - Logging: `logging` configurado en `main.py` y módulos.
   - Rate limiting: `slowapi` con `Limiter(key_func=get_remote_address)`.
   - CORS configurado con orígenes locales y `*` (acepta todos) — revisar antes de producción.
   - Health endpoints: `/health` comprueba conexión con Supabase.
   <!-- inferido del código -->

Integraciones externas
----------------------
- Supabase Auth + Postgres (principal integración). <!-- inferido del código -->
- Vercel como plataforma de despliegue (ver `vercel.json`). <!-- inferido del código -->
- (Planificado) Worker/servicio de notificaciones para procesar recordatorios (pendiente). <!-- confirmado por Andres -->

Flujos de datos críticos
------------------------

1. Registro de usuario
   - Cliente -> `POST /api/users` (UserCreate)
   - Backend: verifica unicidad email/avatar en `profiles` -> `supabase.auth.sign_up(...)` -> upsert en `profiles` (por trigger o manual)
   - Respuesta: info básica del usuario y mensaje de éxito.
   <!-- inferido del código -->

2. Login
   - Cliente -> `POST /api/auth/login` (UserLogin)
   - Backend: `supabase.auth.sign_in_with_password()` -> si OK devuelve access/refresh tokens y metadata/profile.
   - `get_current_user` para endpoints protegidos usa `supabase.auth.get_user(token)`.
   <!-- inferido del código -->

3. Crear tarea / crear recordatorios
   - Cliente -> `POST /api/tasks/` con `due_date` y `reminders` config.
   - Backend: genera UUID, inserta en `tasks`, calcula `remind_at = due_date - offset` y crea filas en `reminders` asociadas.
   - NOTA: procesamiento de envío (cambio de `pending` a `sent`) requiere worker externo (pendiente).
   <!-- inferido del código -->

Decisiones de diseño y justificación
------------------------------------

- Supabase como single source-of-truth:
  - Ventaja: Auth + DB + RLS centralizados y fáciles de usar con `supabase-py`.
  - Desventaja: dependencias de API de supabase en el backend (ej. llamadas a `supabase.auth...`) y versión de cliente.
  <!-- inferido del código -->

- Rate limiting con SlowAPI:
  - Protege endpoints públicos (login, register) y evita abuso.
  <!-- inferido del código -->

- Separación por routers (modular):
  - Facilita mantener dominio claramente separado (auth, tasks, notes, events, reminders, relations).
  - Facilita tests y refactors (se observa refactor en events).
  <!-- inferido del código -->

Seguridad y secretos
-------------------
- Variables críticas: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (o `SERVICE_ROLE`, `SUPABASE_ANON_KEY`).
  - `database.py` intenta múltiples nombres de variable y carga `.env` mediante python-dotenv.
  <!-- inferido del código -->
- RLS / Policies:
  - RLS está habilitado en scripts SQL, pero según confirmación actual RLS está desactivado en el entorno de desarrollo. <!-- confirmado por Andres -->
  - <!-- TODO: verificar --> Confirmar antes de activar en producción: las policies deben permitir que el backend (service role) funcione correctamente sin abrir excesivamente el acceso.

Escalado y despliegue
---------------------
- Despliegue actual: Vercel con `main.py` (ver `vercel.json`).
  - Build: `@vercel/python` apunta a `main.py`.
  - Considerar: Vercel limita el modelo de ejecución (funciones serverless). Asegurarse que latencia y timeouts no limiten operaciones largas.
  <!-- inferido del código -->

- Recomendaciones:
  - Para alta carga y workers de recordatorios, desplegar un worker separado (ej. small VM, serverless function con scheduler, o Background job runner) que consulte `reminders` y envíe notificaciones.
  - Externalizar tasks de largo procesamiento (si aparece IA para summary) a colas (Redis/RQ, Celery) o jobs serverless.

Observabilidad y pruebas
------------------------
- Logging: ya presente (python logging). Aumentar trazabilidad (request id, correlation id) para debug en producción.
- Tests: hay scripts en `tests/` (pruebas de límite/estrés). Añadir CI para ejecutar tests en PRs.
- Health checks: `/health` ya comprueba conexión Supabase y expone `supabase_connected` y `supabase_url` (sensible: evitar exponer URL en prod).

Limitaciones y riesgos identificados
------------------------------------
- Worker de recordatorios no implementado — recordatorios quedan en BD en `pending` sin consumidor. <!-- confirmado por Andres -->
- RLS desactivado en entorno de desarrollo — riesgo si se activa sin revisar policies. <!-- confirmado por Andres -->
- CORS configurado con `*` en `main.py` — riesgo de seguridad si se despliega sin restricciones.
- Dependencia fuerte en `supabase-py` API: cambios en client o en Supabase API pueden romper flujos (e.g. métodos de refresh_session/ sign_up que cambian). <!-- inferido del código -->
- Campo `icon` en `TagUpdate` está pendiente de exponer para edición según rules. <!-- inferido del código -->

Design tokens (placeholders)
---------------------------
Aunque este repositorio es backend-only, incluyo un bloque de design tokens para cuando el frontend sea actualizado/consistente con el backend (usados para coloreado de tags y estilos del UI). Ponerlos en `docs/design-tokens.json` o similar cuando se necesite:

```json
{
  "colors": {
    "tag_default": "#808080" /* inferido */,
    "brand_primary": "#0d6efd" /* TODO: verificar */
  },
  "spacing": {
    "small": "4px",
    "base": "8px",
    "large": "16px"
  },
  "fonts": {
    "base": "Inter, system-ui, sans-serif" /* TODO: verificar */
  }
}
```
<!-- inferido del código -->

Endpoints y contratos (resumen)
------------------------------
- Auth: `/api/auth/*`, `/api/users/*` (registro, login, refresh, me, password, avatar)
- Tags: `/api/tags/*` (CRUD)
- Tasks: `/api/tasks/*` (CRUD, list con paginación cursor y filtros, /{id}/related)
- Notes: `/api/notes/*` (CRUD, /{id}/summary, /{id}/related)
- Events: `/api/events/*` (CRUD, reminders, tags, related)
- Reminders: `/api/reminders/*` (listar, patch, delete)
- Relations: `/api/relations/*` (link/unlink endpoints para tareas/notas/eventos)
<!-- inferido del código -->

Operación diaria / Runbook corta
-------------------------------
- Iniciar en local:
  - Crear `.env` con `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY`.
  - `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
  - `uvicorn main:app --reload`
  <!-- inferido del código -->
- Health:
  - `GET /health` — revisa conexión con Supabase
  - `GET /tables` — requiere que exista RPC `get_tables` en Supabase (nota: `tables` endpoint sugiere ejecutar SQL helper)
- Despliegue:
  - Commit/PR a `development`, revisar cambios de documentación, luego merge a `production` (flujo ya adoptado en repo).

Checklist antes de merge (documentación-only change)
---------------------------------------------------
(La petición del workflow pedía: actualizar docs, push en `development`, verificar que no haya cambios funcionales y luego merge a `production`.)

- [ ] Confirmar que los cambios en `development` son solamente docs (no modificaciones en `api/*.py`, `*/schemas.py`, `database.py`, migraciones, etc.). <!-- TODO: verificar -->
- [ ] Ejecutar tests (si procede) en CI.
- [ ] Revisar `vercel.json` y CORS antes de merge a `production`.
- [ ] Confirmar que RLS debe permanecer desactivado en producción o activar policies con testing controlado. <!-- confirmado por Andres / TODO: verificar en entorno real -->

Ambigüedades / TODOs
--------------------
- <!-- TODO: verificar --> Confirmar en staging si RLS está activado o no y si al activarlo las policies actuales funcionan con el service role.
- <!-- TODO: verificar --> Confirmar la lista final de environment variables secretas que no están en `.env.example`.
- <!-- TODO: verificar --> Revisar que `docs/design.md` y `docs/spec.md` estén alineados con el código actual.
- <!-- TODO: verificar --> Agregar worker/arquitectura de background jobs para recordatorios y definir donde será desplegado.
- <!-- TODO: verificar --> Añadir `icon` a `TagUpdate` si se quiere permitir edición desde UI (pendiente detectado en rules).

Notas finales
-------------
- Events está terminado y el `rules.md` anterior está desactualizado. <!-- confirmado por Andres -->
- `improvement_insights` se deja fuera por ahora según indicación. <!-- confirmado por Andres -->
- Worker de notificaciones está planeado pero no implementado. <!-- confirmado por Andres -->

Documentos relacionados
----------------------
- `README.md` — guía de inicio rápido y variables de entorno. <!-- inferido del código -->
- `docs/design.md`, `docs/spec.md`, `docs/blueprint.md` — revisar antes de merge; historial en Git si no hay changelog dedicado. <!-- inferido del código -->

--------------------------------------------------------------------------------
Fin del documento
--------------------------------------------------------------------------------