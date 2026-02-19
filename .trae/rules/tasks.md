---
alwaysApply: false
scope: tasks
---

# Tasks
- Endpoints: POST /api/tasks, GET /api/tasks, GET /api/tasks/{id}, PATCH /api/tasks/{id}, DELETE /api/tasks/{id}, GET /api/tasks/{id}/related, POST /api/tasks/{id}/tags, DELETE /api/tasks/{id}/tags/{tag_id}, POST /api/tasks/notes, DELETE /api/tasks/{id}/notes/{note_id}.
- Listado paginado con cursor (due_date del último item).
- view=home: pendientes atrasadas + próximos 7 días; completadas solo dentro de ventana; sin due_date excluidas; pendientes atrasadas primero, luego pendientes futuras, luego completadas futuras (todas por due_date asc).
- view=tasks, tab=pending: solo pendientes; atrasadas primero por due_date asc, luego futuras por due_date asc, luego sin due_date al final.
- view=tasks, tab=completed: solo completadas; por due_date desc (más recientes primero), luego sin due_date al final.
- GET /api/tasks y GET /api/tasks/{id} retornan la tarea sin tags, notes ni events.
- GET /api/tasks/{id}/related retorna tags, notes y events vinculados a la tarea.
- POST /api/tasks retorna la tarea creada sin tags, notes ni events.
