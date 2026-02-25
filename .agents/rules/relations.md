---
alwaysApply: false
description: Reglas de relaciones entre entidades (tareas, notas, eventos).
---
# Relations
- Endpoints: POST /api/relations/task-note, DELETE /api/relations/task-note, POST /api/relations/task-event, DELETE /api/relations/task-event, POST /api/relations/note-event, DELETE /api/relations/note-event.
- Cada endpoint recibe los dos IDs de los elementos a vincular/desvincular en el body.
- El backend valida que ambos elementos existan y pertenezcan al usuario autenticado antes de crear o eliminar la relación.
- Las relaciones son simétricas: no hay dueño. Tarea, nota y evento son iguales en la vinculación.
- Estos endpoints reemplazan y migran POST /api/tasks/notes y DELETE /api/tasks/{id}/notes/{note_id} que quedan deprecados.
- Las relaciones de etiquetas (tags) NO se manejan aquí; cada entidad es dueña de su conexión con tags (POST /api/tasks/{id}/tags, POST /api/notes/{id}/tags, etc.).