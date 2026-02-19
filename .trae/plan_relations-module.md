Plan: Módulo Relations con hard delete en Tasks
=============================================

Contexto
--------
- Nuevo módulo neutral `relations` para vincular tareas, notas y eventos.
- Endpoints objetivo:
  - POST   /api/relations/task-note
  - DELETE /api/relations/task-note
  - POST   /api/relations/task-event
  - DELETE /api/relations/task-event
  - POST   /api/relations/note-event
  - DELETE /api/relations/note-event
- Migración con **hard delete** de:
  - POST   /api/tasks/notes
  - DELETE /api/tasks/{id}/notes/{note_id}

Fase 1 – Revisión y diseño fino
-------------------------------
- Verificar estado actual de:
  - `relations/rules.md` y `.trae/rules/relations.md` (hecho, están alineados).
  - Tablas de BD: `task_notes`, `event_tasks`, `event_notes` (ya existen).
  - Implementación actual en código:
    - Confirmar existencia (o ausencia) de `relations/api.py` y `relations/schemas.py`.
- Decisiones de contrato:
  - Todos los endpoints usan body con los dos IDs involucrados.
  - Respuestas:
    - POST: 201 + `{ "message": "... vinculadas exitosamente" }`.
    - DELETE: 200 + `{ "message": "... eliminada exitosamente" }`.
  - Errores:
    - 404 si alguna entidad no existe / no pertenece al usuario (POST) o si la relación no existe (DELETE).
    - 409 si la vinculación ya existe (POST).

Fase 2 – Implementar módulo Relations
-------------------------------------
- Crear/ajustar `relations/schemas.py`:
  - Modelos:
    - `TaskNoteLink` con `task_id`, `note_id`.
    - `TaskEventLink` con `task_id`, `event_id`.
    - `NoteEventLink` con `note_id`, `event_id`.
- Crear/ajustar `relations/api.py`:
  - Configuración:
    - `router = APIRouter()` con prefix `/api/relations` desde el `main`.
  - Endpoints:
    - POST /task-note:
      - Validar que la tarea y la nota existan y pertenezcan al usuario.
      - Verificar si ya existe fila en `task_notes`; si existe, 409.
      - Insertar fila en `task_notes`; devolver 201 + mensaje.
    - DELETE /task-note:
      - Verificar existencia de fila en `task_notes`; si no existe, 404.
      - Eliminar fila; devolver 200 + mensaje.
    - POST /task-event:
      - Igual patrón contra tabla `event_tasks`.
    - DELETE /task-event:
      - Igual patrón contra `event_tasks`.
    - POST /note-event:
      - Igual patrón contra tabla `event_notes`.
    - DELETE /note-event:
      - Igual patrón contra `event_notes`.
- Infra:
  - Registrar el router en el `main` (o módulo central) con el prefix adecuado.
- Validación:
  - Probar manualmente los endpoints con supuestos IDs válidos/invalidos (404, 409).
  - Verificar que las relaciones se reflejan correctamente en:
    - `GET /api/tasks/{id}/related`.
    - `GET /api/notes`.
    - `GET /api/events`.

Fase 3 – Hard delete en Tasks
-----------------------------
- En `tasks/api.py`:
  - Eliminar completamente:
    - POST   /api/tasks/notes.
    - DELETE /api/tasks/{id}/notes/{note_id}.
  - Asegurarse de que ninguna otra función interna dependa de esos handlers.
- En `tasks/rules.md`:
  - Eliminar la sección:
    - "Vincular nota a tarea" (POST /api/tasks/notes).
    - "Desvincular nota de tarea" (DELETE /api/tasks/{id}/notes/{note_id}).
  - En la sección de `/related`, dejar claro que la lectura de notas/eventos sigue funcionando pero las relaciones se gestionan vía `Relations`.
- En `.trae/rules/tasks.md`:
  - Asegurar que el resumen corto ya no menciona estos endpoints de Tasks.
- En `.trae/rules/relations.md`:
  - Mantener la nota de que estos endpoints de Tasks están deprecados/eliminados y que las relaciones se manejan exclusivamente en Relations.

Fase 4 – Revisión cruzada de lectura de relaciones
--------------------------------------------------
- `GET /api/tasks/{id}/related`:
  - Verificar que está usando joins contra:
    - `task_notes(notes(...))`.
    - `event_tasks(events(...))`.
  - Asegurar consistencia con las operaciones del módulo Relations:
    - Si Relations inserta/elimina filas correctamente, `/related` debe reflejar los cambios.
- `GET /api/notes` y `GET /api/events`:
  - Confirmar que sus transforms (tasks, notes, events relacionados) siguen leyendo de:
    - `task_notes`, `event_tasks`, `event_notes`.
  - Ajustar únicamente si hay divergencias de contrato, sin duplicar lógica de creación/eliminación.

Fase 5 – Validación final y limpieza conceptual
-----------------------------------------------
- Ejecutar pruebas manuales de flujo completo:
  - Crear tarea, nota y evento.
  - Vincular/desvincular cada combinación desde `/api/relations/...`.
  - Validar:
    - Lecturas desde `/api/tasks/{id}/related`.
    - Lecturas desde `/api/notes` y `/api/events`.
- Revisar documentación:
  - `relations/rules.md` y `.trae/rules/relations.md` como fuente de verdad para relaciones entre entidades.
  - `tasks/rules.md` y `.trae/rules/tasks.md` sin endpoints de notas heredados.
- Confirmar que no quedan referencias en frontend ni en otros módulos a:
  - POST   /api/tasks/notes.
  - DELETE /api/tasks/{id}/notes/{note_id}.

