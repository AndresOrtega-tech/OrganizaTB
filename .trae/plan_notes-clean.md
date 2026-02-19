Plan: Limpieza del módulo Notes (NoteResponse sin relaciones)
============================================================

Contexto y objetivo
-------------------
- Hoy `NoteResponse` incluye `tags`, `tasks` y `events`. Ver [notes/schemas.py](../notes/schemas.py#L1-L51): los campos `tags`, `tasks`, `events` están embebidos en el schema.
- Los endpoints de notas construyen esas relaciones embebidas en list y get. Ver [notes/api.py](../notes/api.py#L44-L118): se procesan `note_tags`, `task_notes`, `event_notes` y se asignan a `note["tags"]`, `note["tasks"]`, `note["events"]`.
- Reglas vigentes establecen que Notes ya no devuelve relaciones embebidas; se exponen vía `/related`. Ver [notes/rules.md](../notes/rules.md) y [.trae/rules/notes.md](./notes.md).
- Objetivo: limpiar las respuestas de Notes, agregar `/related`, y migrar tags a `POST /api/notes/{id}/tags` con `tag_id` único.

Alcance (archivos afectados)
----------------------------
- `notes/schemas.py`
- `notes/api.py`
- `notes/rules.md` y `.trae/rules/notes.md` (ya están alineados; solo verificar tras cambios)

Decisiones clave
----------------
- Separar datos base vs. relaciones:
  - `NoteResponse`: solo campos base (sin `tags`, `tasks`, `events`).
  - `NoteRelatedResponse`: `tags`, `tasks`, `events` (solo para `/related`).
- Tags en notas:
  - `POST /api/notes/{note_id}/tags` con body `{ "tag_id": "..." }` e idempotencia.
  - `DELETE /api/notes/{note_id}/tags/{tag_id}` como desvinculación.
- GET list con `limit` opcional para respetar reglas.
- Usar el mismo patrón de joins que `tasks/{id}/related` para consistencia (joins embebidos con cleanup).

Fase 1 – Schemas
----------------
1) Modificar `NoteResponse`:
   - Remover campos: `tags`, `tasks`, `events`.
   - Mantener: `id`, `title`, `content`, `summary`, `is_archived`, `user_id`, `media_url`, `created_at`, `updated_at`.
2) Agregar `NoteRelatedResponse`:
   - `tags`: `[TagResponse]`
   - `tasks`: `[TaskSummary]` (id, title, is_completed)
   - `events`: `[EventSummary]` (id, title, start_time)
3) Agregar `NoteAssignTag`:
   - `tag_id: str` (solo uno).
   - El `note_id` vendrá en la ruta.
4) Agregar `NoteSummaryUpdate`:
   - `summary: Optional[str]` (max_length=500).
   - Permite enviar `null` para limpiar el resumen en BD.

Fase 2 – Endpoints Notes
------------------------
1) GET `/api/notes/` (list):
   - Quitar construcción de `tags`, `tasks`, `events` en cada item.
   - Agregar param `limit: Optional[int]` y aplicarlo con `.limit(limit)` si se envía.
   - Mantener filtros `is_archived`, `tag_ids` (AND), orden por `updated_at` (desc default).
2) GET `/api/notes/{id}` (detail):
   - Retornar solamente `NoteResponse` sin relaciones embebidas.
3) POST `/api/notes/` (create):
   - Responder `NoteResponse` sin relaciones.
4) PATCH `/api/notes/{id}` (update):
   - Responder `NoteResponse` sin relaciones.
5) PATCH `/api/notes/{id}/summary` (nuevo):
   - Body `{ "summary": "Nuevo resumen" }` o `{ "summary": null }`.
   - Valida propiedad de la nota.
   - Si `summary` es string, lo guarda; si es `null`, deja `summary` en `NULL`.
   - Devuelve la nota como `NoteResponse` base.
6) GET `/api/notes/{id}/related` (nuevo):
   - Joins: 
     - `note_tags(tags(id, name, color, icon))`
     - `task_notes(tasks(id, title, is_completed))`
     - `event_notes(events(id, title, start_time))`
   - Transformar a `NoteRelatedResponse` limpiando estructuras anidadas como en `tasks/{id}/related`.
7) POST `/api/notes/{note_id}/tags` (migración):
   - Body `{ "tag_id": "..." }`.
   - Validar propiedad de la nota.
   - Idempotencia: si ya existe (`note_tags`), devolver `{"message": "...", "assigned": 0}`; si inserta, `assigned: 1`.
8) DELETE `/api/notes/{note_id}/tags/{tag_id}`:
   - Validar propiedad de la nota y borrar relación en `note_tags`.
9) Eliminar/Deprecar `POST /api/notes/tags` (batch) si existe.

Fase 3 – Documentación
----------------------
- Verificar que `notes/rules.md` y `.trae/rules/notes.md` ya reflejan:
  - `NoteResponse` sin embebidos.
  - Presencia de `/related`.
  - Nuevos endpoints de tags.
- Ajustar solo si se detecta desalineación post-cambio.

Fase 4 – Validación rápida
--------------------------
- Crear una nota; verificar POST/GET sin relaciones embebidas.
- Asignar tag con `POST /api/notes/{id}/tags`; verificar idempotencia y `DELETE` funciona.
- Vincular task/event vía `/api/relations/*` y verificar que `/api/notes/{id}/related` refleja cambios.
- Probar `GET /api/notes?limit=3` respetando orden y filtros.

Riesgos y mitigaciones
----------------------
- Frontend esperando campos embebidos: coordinar migración y aprobar PR conjunto; las rules ya documentan el nuevo contrato.
- Performance de /related: mantener joins embebidos en una sola consulta y limpiar en Python como en tasks.
