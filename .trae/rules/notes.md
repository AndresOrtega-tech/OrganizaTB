---
alwaysApply: false
description: Reglas de notas con endpoints CRUD y relaciones.
---
# Notes
- Endpoints: POST /api/notes, GET /api/notes, GET /api/notes/{id}, PATCH /api/notes/{id}, PATCH /api/notes/{id}/summary, DELETE /api/notes/{id}, GET /api/notes/{id}/related, POST /api/notes/{id}/tags, DELETE /api/notes/{id}/tags/{tag_id}.
- Listado sin paginación de cursor; el frontend controla `limit` y `sort_by`/`order`.
- Por defecto retorna solo notas no archivadas (`is_archived=false`). El filtro debe mandarse explícito para ver archivadas.
- GET /api/notes y GET /api/notes/{id} retornan la nota sin tags, tasks ni events.
- PATCH /api/notes/{id}/summary permite crear/actualizar el resumen; si `summary=null` limpia el campo en BD.
- GET /api/notes/{id}/related retorna tags, tasks y events vinculados a la nota.
- POST /api/notes retorna la nota creada sin tags, tasks ni events.
- Las vinculaciones con tasks y events se manejan desde /api/relations, NO desde este módulo.
- Las etiquetas (tags) sí son propiedad de la nota: se asignan y desvinculan desde este módulo.
