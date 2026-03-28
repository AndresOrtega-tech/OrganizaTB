# Design — OrganizaT API
<!-- inferido del código -->

Última actualización: 2026-03-27 (CR-001: Docker + Kubernetes — completado)

Resumen
-------
Documento de diseño técnico que describe la arquitectura real encontrada en el código, los componentes principales, flujos de datos y decisiones relevantes para la operación y evolución del backend OrganizaT.

Elementos marcados:
- <!-- inferido del código --> lo que deduje del código.
- <!-- confirmado por Andres --> lo que el maintainer confirmó en la conversación.
- <!-- TODO: verificar --> puntos que requieren confirmación manual (RLS, procesos externos, etc.).

Arquitectura general
--------------------
Arquitectura: Monolito backend en Python ejecutándose como una aplicación FastAPI, con Supabase (Postgres + Auth) como backend de persistencia y auth.

Deploy targets:
- **Vercel** (actual): `@vercel/python` con `main.py` como entrypoint — serverless.
- **Docker + Kubernetes** (CR-001 ✅ completado): imagen Docker corriendo uvicorn, orquestada con Helm en Kubernetes, validada localmente con Minikube. <!-- CR-001 -->
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
**Opción A — Vercel (actual)**
- Despliegue actual: Vercel con `main.py` (ver `vercel.json`).
  - Build: `@vercel/python` apunta a `main.py`.
  - Considerar: Vercel limita el modelo de ejecución (funciones serverless). Asegurarse que latencia y timeouts no limiten operaciones largas.
  <!-- inferido del código -->

**Opción B — Docker + Kubernetes (CR-001)** <!-- CR-001 -->
- La app corre como proceso continuo dentro de un contenedor Docker (no serverless).
- Orquestada con Helm; validada localmente con Minikube.
- El proveedor cloud de K8s está por definirse (GKE, EKS, AKS, DigitalOcean, etc.).
- Ramas dedicadas: `v_docker_dev` (trabajo) → `v_docker_prod` (estable).

- Recomendaciones:
  - Para alta carga y workers de recordatorios, desplegar un worker separado (ej. small VM, serverless function con scheduler, o Background job runner) que consulte `reminders` y envíe notificaciones.
  - Externalizar tasks de largo procesamiento (si aparece IA para summary) a colas (Redis/RQ, Celery) o jobs serverless.

---

Deploy alternativo: Docker + Kubernetes — Detalle (CR-001)
----------------------------------------------------------
<!-- CR-001 -->

### Dockerfile
```
Base image:  python:3.12-slim
WORKDIR:     /app
COPY:        requirements.txt → pip install → copiar código fuente
EXPOSE:      8000
CMD:         uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
```
- Variables de entorno inyectadas en runtime desde K8s Secrets (no desde `.env`).
- `python-dotenv` / `database.py` ya manejan el fallback a env vars del sistema → compatible.
- `.dockerignore` excluye: `venv/`, `.env*`, `__pycache__/`, `*.pyc`, `tests/`, `docs/`, `.git/`.

### Estructura del Helm chart
```
helm/
└── organizat/
    ├── Chart.yaml              ← metadata del chart
    ├── values.yaml             ← valores default
    ├── values-dev.yaml         ← override Minikube (imagePullPolicy: Never, replicas: 1)

    └── templates/
        ├── _helpers.tpl        ← helpers estándar (fullname, labels)
        ├── deployment.yaml     ← K8s Deployment con liveness/readiness probes
        ├── service.yaml        ← K8s Service (NodePort en dev)
        ├── secret.yaml         ← K8s Secret (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        ├── configmap.yaml      ← K8s ConfigMap (config no sensible)
        └── NOTES.txt           ← instrucciones post-install
```

### Health / Readiness probes
- El endpoint `GET /health` ya existe en la API y devuelve `{"status": "ok", "supabase_connected": bool}`.
- Se usa como `livenessProbe` y `readinessProbe` en el Deployment de Kubernetes.
- Esto garantiza que K8s reinicia pods en mal estado y no enruta tráfico a pods no listos.

### Arquitectura K8s (vista simplificada)
```
Minikube / Cluster K8s
└── Namespace: organizat
    ├── Secret: organizat-secrets          ← SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
    ├── ConfigMap: organizat-config        ← config no sensible
    ├── Deployment: organizat-api
    │   └── Pod(s): organizat-api-xxxxx
    │       └── Container: organizat-api  ← imagen Docker
    │           ├── liveness:  GET /health
    │           ├── readiness: GET /health
    │           └── envFrom:   Secret + ConfigMap
    └── Service: organizat-svc
    └── NodePort (dev)
```

### Flujo local con Minikube
```bash
# 1. Iniciar Minikube
minikube start

# 2. Apuntar Docker al daemon de Minikube (imagen local sin registry externo)
eval $(minikube docker-env)

# 3. Build de la imagen
docker build -t organizat-api:local .

# 4. Instalar Helm chart con valores de dev
helm install organizat ./helm/organizat \
  -f helm/organizat/values-dev.yaml \
  --set secrets.supabaseUrl="$SUPABASE_URL" \
  --set secrets.supabaseKey="$SUPABASE_SERVICE_ROLE_KEY"

# 5. Verificar
kubectl get pods
kubectl port-forward svc/organizat-svc 8000:8000
curl localhost:8000/health
```
El script `scripts/minikube-setup.sh` automatiza estos pasos.

### Gestión de secretos en K8s
- **Nunca** en `values.yaml` ni commiteados en el repo.
- Se pasan al instalar el chart via `--set secrets.*` o mediante un archivo local `secrets.local.yaml`
  que está en `.gitignore`.
- En producción cloud: la estrategia de secrets se define cuando se elija el proveedor (GKE, EKS, etc.).

### Separación de tracks de deploy
- `vercel.json` **solo existe** en las ramas `production` y `development`.
- Las ramas `v_docker_dev` y `v_docker_prod` son exclusivas de la infra Docker/K8s — no incluyen `vercel.json`.
- Los dos tracks son independientes:
  - Features/lógica: `development` → `production`
  - Infra Docker/K8s: `v_docker_dev` → `v_docker_prod`

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

Riesgos adicionales — Docker + Kubernetes (CR-001): <!-- CR-001 -->
- Secrets expuestos en `values.yaml` si no se tiene disciplina → nunca poner valores sensibles en values files.
- Imagen Docker pesada si no se usa `.dockerignore` correctamente → build lento y pull lento en K8s.
- Diferencia de comportamiento Vercel (serverless, stateless por request) vs Docker (proceso continuo)
  → validar con health check y smoke tests antes de mergear a `v_docker_prod`.
- Minikube ≠ cloud real (networking, ingress, storage) → Helm chart diseñado portable; `values-prod.yaml`
  se agrega en CR posterior cuando se defina el proveedor cloud.



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
- <!-- TODO: verificar --> Revisar que la nueva documentación añadida en `docs/ARCHITECTURE.md`, `docs/SPECS.md` esté alineada con el código actual (parece que se añadió en development).
- <!-- TODO: verificar --> Agregar worker/arquitectura de background jobs para recordatorios y definir donde será desplegado.
- <!-- TODO: verificar --> Añadir `icon` a `TagUpdate` si se quiere permitir edición desde UI (pendiente detectado en rules).

Notas finales
-------------
- Events está terminado y el `rules.md` anterior está desactualizado. <!-- confirmado por Andres -->
- `improvement_insights` se deja fuera por ahora según indicación. <!-- confirmado por Andres -->
- Worker de notificaciones está planeado pero no implementado. <!-- confirmado por Andres -->
- Deploy Docker + Kubernetes completado (CR-001) ✅: Dockerfile, Helm chart, validado en Minikube. <!-- CR-001 -->

Documentos relacionados
----------------------
- `README.md` — guía de inicio rápido y variables de entorno. <!-- inferido del código -->
- `docs/ARCHITECTURE.md`, `docs/SPECS.md`, `docs/CHANGELOG.md` — versiones en `development` que deben revisarse antes de merge. <!-- inferido del código -->

--------------------------------------------------------------------------------
Fin del documento
--------------------------------------------------------------------------------