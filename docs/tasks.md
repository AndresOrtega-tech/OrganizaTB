# Task Board: OrganizaT

> **Basado en:** init-pipeline (proyecto existente)  
> **Total de tasks:** 8 completadas + 9 pendientes

---

## ✅ Features ya implementadas
> Estas features existen en el código. No hay que implementarlas.

- [x] **IMPL-001** — Auth (registro, login, refresh, reset, perfil)
  - **Estado:** implementado
  - **Archivos principales:** `auth/api.py`, `auth/schemas.py`, `auth/dependencies.py`, `main.py`
  - **Notas:** Usa Supabase Auth como proveedor; backend actúa como intermediario para sign_up / sign_in / refresh. Tokens devueltos por Supabase. <!-- inferido del código -->

- [x] **IMPL-002** — CRUD Tags (catálogo de etiquetas por usuario)
  - **Estado:** implementado
  - **Archivos principales:** `tags/api.py`, `tags/schemas.py`, `database.txt` (tabla `tags`)
  - **Notas:** `name` único por usuario (constraint en BD). `icon` existe en BD y en `TagResponse` pero edición parcial en schemas (pendiente menor documentado). <!-- inferido del código -->

- [x] **IMPL-003** — CRUD Tasks (crear, listar con paginación cursor, update, delete)
  - **Estado:** implementado
  - **Archivos principales:** `tasks/api.py`, `tasks/schemas.py`, `database.txt` (tabla `tasks`), `supabase/migrations/*`
  - **Notas:** Soporta `view=home` y `view=tasks` con `tab` (pending/completed), filtros por `tag_ids` (AND), `priority` y paginación por cursor. Recordatorios se generan automáticamente desde la creación/actualización de tareas. <!-- inferido del código -->

- [x] **IMPL-004** — CRUD Notes (archivado, summary, tags)
  - **Estado:** implementado
  - **Archivos principales:** `notes/api.py`, `notes/schemas.py`, `database.txt`
  - **Notas:** `summary` pensado para integración IA futura; listing filtra por `is_archived`. <!-- inferido del código -->

- [x] **IMPL-005** — CRUD Events (crear, listar, update, delete)
  - **Estado:** implementado
  - **Archivos principales:** `events/api.py`, `events/schemas.py`, `database.txt`, `supabase/migrations/20260204_create_events_module.sql`
  - **Notas:** Confirmado que `events` ya está terminado y alineado con patrones de `tasks/notes`. <!-- confirmado por Andres -->

- [x] **IMPL-006** — Reminders (list, update status/date, delete)
  - **Estado:** implementado (API para administrar reminders)
  - **Archivos principales:** `reminders/api.py`, `reminders/schemas.py`, `database.txt`, `supabase/migrations/20260204_create_reminders_table.sql`
  - **Notas:** Recordatorios se generan desde tasks/events y el endpoint permite filtrar por estado/rango. Worker para enviar notificaciones NO implementado (pendiente). <!-- inferido del código -->

- [x] **IMPL-007** — Relations (vinculaciones task↔note, task↔event, note↔event)
  - **Estado:** implementado
  - **Archivos principales:** `relations/api.py`, `relations/schemas.py`, `database.txt` (tablas `task_notes`, `event_tasks`, `event_notes`)
  - **Notas:** El módulo valida pertenencia del usuario a ambas entidades antes de vincular; retorna 409 si ya existe. <!-- inferido del código -->

- [x] **IMPL-008** — Health and infra endpoints
  - **Estado:** implementado
  - **Archivos principales:** `main.py`, `database.py`, `vercel.json`
  - **Notas:** Endpoints `/`, `/health`, `/tables` disponibles; Vercel configurado para desplegar `main.py`. <!-- inferido del código -->

---

## 📋 Tasks pendientes
> Lo que falta implementar, corregir o mejorar según el análisis.

- [ ] **TASK-001** — Worker de notificaciones para reminders
  - **Descripción:** Implementar un worker (cron/job/worker) que procese recordatorios pendientes (`status=pending`) y ejecute el envío (email/push) y actualice `status` a `sent` o `failed`.
  - **Archivos involucrados:** crear carpeta `workers/` (ej. `workers/reminders_worker.py`), integrar con job runner (Celery / RQ / Cron) o servicio externo.
  - **Depende de:** Ninguna (pero coordinar con infra/deployment)
  - **Criterio de done:** Worker procesa reminders de prueba, actualiza `status` y logs; pruebas unitarias de comportamiento; documentación en `docs/`.

- [ ] **TASK-002** — Check constraint en BD: (task_id XOR event_id) para `reminders`
  - **Descripción:** Añadir constraint SQL que garantice que cada reminder apunte a exactamente una fuente (tarea o evento).
  - **Archivos involucrados:** `supabase/migrations/*` (nueva migration)
  - **Depende de:** Ninguna
  - **Criterio de done:** Nueva migration aplicada en staging; tests que verifiquen inserciones inválidas rechazadas.
  - **Notas:** El `database.txt` y las migraciones ya mencionan la necesidad de esto. <!-- TODO: verificar -->

- [ ] **TASK-003** — Agregar `icon` a `TagUpdate` y permitir editar icon
  - **Descripción:** Actualizar `tags/schemas.py` (`TagUpdate`) para incluir `icon`, y actualizar `tags/api.py` para aceptar cambios.
  - **Archivos involucrados:** `tags/schemas.py`, `tags/api.py`
  - **Depende de:** Ninguna
  - **Criterio de done:** `PATCH /api/tags/{id}` permite cambiar `icon`; tests cubriendo validación.

- [ ] **TASK-004** — Activar y validar RLS en Supabase (políticas)
  - **Descripción:** Revisar y activar Row Level Security en el proyecto Supabase, asegurando que todas las políticas necesarias estén definidas y que los endpoints sigan funcionando.
  - **Archivos involucrados:** `database.txt` (políticas), documentación de despliegue
  - **Depende de:** Validación en staging
  - **Criterio de done:** RLS activa en staging, pruebas de integración pasan; rollback procedure documentado.
  - **Notas:** Actualmente RLS está desactivado en desarrollo. <!-- confirmado por Andres -->

- [ ] **TASK-005** — Integración e2e de auth + supabase (cobertura de flows)
  - **Descripción:** Añadir pruebas e2e que validen registro, login, refresh y llamadas autenticadas a endpoints clave (`/api/tasks`, `/api/notes`).
  - **Archivos involucrados:** `tests/`, CI pipeline (if present)
  - **Depende de:** ENV de testing con supabase de staging
  - **Criterio de done:** Suite e2e en CI que pasa contra ambiente de pruebas.

- [ ] **TASK-006** — Revisar y consolidar documentación en `docs/`
  - **Descripción:** Alinear `README.md` con `docs/SPECS.md`, `docs/ARCHITECTURE.md` y `docs/CHANGELOG.md`. Generar `project-brief.md`, `spec.md`, `design.md`, `blueprint.md` (este workflow).
  - **Archivos involucrados:** `README.md`, `docs/*.md`
  - **Depende de:** Validación de que no hay cambios funcionales en el branch.
  - **Criterio de done:** Docs actualizadas en `development`; PR listo para merge.

- [ ] **TASK-007** — Crear CI check que asegure "docs-only" commit antes de merge
  - **Descripción:** Añadir un step en CI que verifique que el commit o PR contiene solo cambios en documentación si se etiqueta como "docs-only"; si no, correr la suite completa.
  - **Archivos involucrados:** `.github/workflows/*` o `.windsurf/workflows/*`
  - **Depende de:** Infra CI accesible
  - **Criterio de done:** PR marcados como docs-only pueden auto-merge tras checks.

- [ ] **TASK-008** — Implementar módulo `improvement_insights` (postergado)
  - **Descripción:** Diseñar y exponer API para `improvement_insights` (create / list / mark-read) cuando se decida priorizar.
  - **Archivos involucrados:** nueva carpeta `insights/`, migraciones si aplica
  - **Depende de:** Prioridad del roadmap
  - **Criterio de done:** Endpoints implementados + DB migrada + tests.
  - **Notas:** Por ahora no es prioridad. <!-- confirmado por Andres -->

- [ ] **TASK-009** — Smoke tests y validación antes de merge a `production`
  - **Descripción:** Antes de mergear `development` → `production`, ejecutar checklist:
    - Asegurar que los cambios son SOLO documentacion (diff de archivos funcionales = 0)
    - Ejecutar test suite local/CI
    - Validar health endpoints y conexión a supabase/no secrets leaked
  - **Archivos involucrados:** script de verificación (ej. `scripts/premerge_check.sh`), CI
  - **Depende de:** `TASK-006`, `TASK-005`
  - **Criterio de done:** Checklist automatizado pasa; PR aprobado y merge ejecutado.

---

## Orden de ejecución sugerido
1. `TASK-006` — Actualizar y consolidar docs en `development` (porque ya acordaste que los cambios actuales son de documentación).
2. `TASK-009` — Ejecutar smoke tests y validaciones locales/CI para confirmar "docs-only".
3. Si (2) es OK: push de `development` y crear PR → merge a `production`.
4. `TASK-007` — Añadir CI guard (opcional) para futuros merges docs-only.
5. `TASK-002` y `TASK-003` — Backlog técnico (BD: constraint; TagUpdate icon).
6. `TASK-001` — Implementar worker de reminders (recomendado después de estabilizar RLS y migraciones).
7. `TASK-004` — Activar y validar RLS en Supabase (hacerlo en staging primero).
8. `TASK-005` y `TASK-008` — Tests e insights según prioridad del roadmap.

---

Notas finales:
- He marcado con `<!-- TODO: verificar -->` los items que requieren confirmar estado en la BD o migraciones (ej. constraint XOR en `reminders`). <!-- TODO: verificar -->
- Confirmaciones que me diste ya han sido registradas en las tasks relevantes:
  - RLS desactivado en desarrollo. <!-- confirmado por Andres -->
  - `events` concluido (rules.md estaba desactualizado). <!-- confirmado por Andres -->
  - `improvement_insights` queda postergado. <!-- confirmado por Andres -->
  - Worker para reminders planificado pero no implementado. <!-- confirmado por Andres -->

Si quieres, ahora:
- Procedo a generar `docs/*` (los demás archivos del pipeline) y te doy el diff listo para commit; o
- Produzco un checklist de comandos para ejecutar localmente antes de push/merge (push a `development`, abrir PR, ejecutar tests). 

Dime cuál prefieres y la sigo.