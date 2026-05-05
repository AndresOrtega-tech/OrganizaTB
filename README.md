# Informe técnico — OrganizaT API

**Tipo:** backend REST (productividad personal)  
**Repositorio:** monolito FastAPI + Supabase (PostgreSQL + Auth)  
**Despliegue objetivo:** Vercel (`@vercel/python`, entrada `main.py`)

---

## 1. Resumen ejecutivo

OrganizaT expone una API centralizada para gestionar **tareas, notas, eventos, recordatorios y relaciones** entre entidades, con autenticación vía Supabase Auth. El servicio está pensado para ser consumido por un frontend web y, en el futuro, por workers o integraciones internas.

**Estado:** funcional en alcance MVP descrito en `docs/spec.md` y `docs/tasks.md`.  
**Gaps principales:** worker de notificaciones para recordatorios no implementado; RLS en Supabase desactivado en desarrollo; sin archivo `docs/CHANGELOG.md` — el historial de cambios está en el historial de Git.

---

## 2. Alcance y responsabilidades

| Ámbito | Incluido |
|--------|-----------|
| Identidad | Registro, login, refresh, perfil, avatar, cambio y reset de contraseña |
| Dominio | Tags, tasks, notes, events, reminders (gestión), relations entre entidades |
| Infra API | Rate limiting (SlowAPI), CORS, health, endpoint opcional `/tables` (RPC) |
| Fuera de alcance inmediato | API `improvement_insights` (tabla existe; sin endpoints); worker de envío de reminders |

---

## 3. Arquitectura (visión)

- **Patrón:** aplicación FastAPI modular por routers (`auth`, `tags`, `tasks`, `notes`, `events`, `reminders`, `relations`).
- **Datos y auth:** cliente `supabase-py` en `database.py`; operaciones contra Postgres y Auth según documentado en `docs/design.md`.
- **Diagrama y decisiones:** `docs/design.md` (flujos críticos, seguridad, escalado).

---

## 4. Stack

| Capa | Tecnología |
|------|------------|
| Runtime | Python 3.x |
| Framework | FastAPI, Uvicorn |
| Límite de peticiones | SlowAPI |
| Datos / Auth | Supabase (PostgreSQL, Auth, RPC opcional) |
| Configuración | python-dotenv |
| Hosting | Vercel (`vercel.json`) |

Dependencias exactas: `requirements.txt`.

---

## 5. Capacidades implementadas (síntesis)

- **Auth:** login, registro, refresh, recuperación de contraseña, perfil y avatar.
- **Tags:** CRUD por usuario con unicidad de nombre.
- **Tasks:** CRUD, vistas `home` / `tasks`, paginación por cursor, filtros, recordatorios derivados de la tarea.
- **Notes:** CRUD, archivado, `summary`, tags.
- **Events:** CRUD con recordatorios y tags.
- **Reminders:** listado y actualización (origen: tasks/events; no hay proceso que envíe notificaciones).
- **Relations:** vínculos task↔note, task↔event, note↔event.

Detalle de rutas, query params y modelos Pydantic: **`docs/spec.md`**.

---

## 6. Riesgos, limitaciones y deuda técnica

Resumen alineado con `docs/blueprint.md` y `docs/project-brief.md`:

- RLS desactivado en el entorno de desarrollo; reactivación en staging/producción requiere pruebas y políticas validadas.
- Sin worker: los recordatorios pueden quedar en estado `pending` sin envío automático.
- Health (`/health`) puede exponer metadatos sensibles — revisar antes de producción.
- CORS debe acotarse a orígenes conocidos en producción.
- Posible constraint pendiente en BD para `reminders` (exactamente una fuente: task XOR event).

---

## 7. Configuración y ejecución local

### Prerrequisitos

- Python 3.x  
- Proyecto Supabase y credenciales  
- Entorno virtual (`venv`)

### Instalación

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Variables de entorno

Crear `.env` en la raíz:

```env
SUPABASE_URL=tu_url_de_supabase
SUPABASE_SERVICE_ROLE_KEY=tu_service_role_key
SUPABASE_ANON_KEY=tu_anon_key_opcional
```

| Variable | Descripción | Requerida |
|----------|-------------|-----------|
| `SUPABASE_URL` | URL del proyecto Supabase | Sí |
| `SUPABASE_SERVICE_ROLE_KEY` | Clave usada por el backend (service role) | Sí |
| `SUPABASE_ANON_KEY` | Alternativa documentada en código / fallback | No |

El cliente en `database.py` puede aceptar alias de nombre de variable según implementación actual; detalle en **`docs/spec.md`** (sección variables).

### Base de datos

- Ejecutar el SQL base (`database.txt`) en el SQL Editor de Supabase según procedimiento del equipo.
- Estado de **RLS:** considerar políticas como trabajo pendiente de endurecimiento; no asumir activación inmediata.

### Servidor de desarrollo

```bash
uvicorn main:app --reload
```

- API: `http://127.0.0.1:8000`  
- OpenAPI / Swagger: `http://127.0.0.1:8000/docs`

---

## 8. Estructura del repositorio

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
├── tests/
├── database.py
├── database.txt
├── main.py
├── requirements.txt
└── vercel.json
```

Reglas por módulo: archivos `*/rules.md`. Plan de pruebas de integración: `tests/plan_pruebas_integracion.md`.

---

## 9. Mapa de documentación

| Documento | Contenido |
|-----------|-----------|
| `docs/project-brief.md` | Contexto de negocio, audiencia, estado del proyecto |
| `docs/spec.md` | Endpoints, modelos, user stories, variables |
| `docs/design.md` | Arquitectura, componentes, flujos, operación |
| `docs/blueprint.md` | Riesgos, mitigaciones, ambigüedades, checklist |
| `docs/tasks.md` | Tareas completadas y backlog priorizado |
| `tests/plan_pruebas_integracion.md` | Plan de pruebas |

**Nota:** No existe `docs/CHANGELOG.md`. Para cambios versionados a nivel de producto, conviene introducirlo o mantener convenciones de commits y releases en Git.

---

## 10. Flujo de ramas y trabajo con IA

- **Ramas:** `development` (trabajo), `production` (estable).
- Cambios de código: validar en `development` antes de promover.
- Comandos de documentación asistida (`/init-docs`, `/update-docs`) si forman parte del flujo del equipo; mantener este README y `docs/` alineados con el código.

---

## 11. Scripts y comandos frecuentes

| Comando | Uso |
|---------|-----|
| `uvicorn main:app --reload` | API en desarrollo |
| `pip install -r requirements.txt` | Dependencias |

---

*Última revisión documental: coherencia de rutas `docs/*.md` y ausencia de `CHANGELOG` centralizado. Para detalle de implementación, la fuente normativa es el código y `docs/spec.md`.*
