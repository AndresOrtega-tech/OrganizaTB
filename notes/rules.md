---
alwaysApply: false
scope: notes
---

# Reglas de Notes

Este documento define el funcionamiento del módulo de notas, incluyendo reglas de filtrado, ordenamiento y contratos de request/response. Mantenerlo actualizado con cualquier cambio en `notes/api.py` y `notes/schemas.py`.

## 1. Endpoints (Notes)

### Crear nota
**POST** `/api/notes/`

**Request:**
```json
{
  "title": "Título opcional",
  "content": "Contenido de la nota",
  "summary": "Resumen opcional (manual o generado por IA)",
  "is_archived": false
}
```

**Response (201 Created):**
```json
{
  "id": "uuid-note",
  "title": "Título opcional",
  "content": "Contenido de la nota",
  "summary": "Resumen opcional",
  "is_archived": false,
  "user_id": "uuid-user",
  "media_url": null,
  "created_at": "2026-02-19T10:00:00Z",
  "updated_at": "2026-02-19T10:00:00Z"
}
```

> La nota se retorna sin `tags`, `tasks` ni `events`.

---

### Listar notas
**GET** `/api/notes/`

**Query params:**
- `is_archived`: `true` | `false` (default `false`)
- `tag_ids`: array de UUID (AND, la nota debe tener TODAS las etiquetas)
- `sort_by`: `updated_at` | `created_at` (default `updated_at`)
- `order`: `asc` | `desc` (default `desc`)
- `limit`: entero positivo (opcional, el frontend lo controla)

**Response (200 OK):**
```json
[
  {
    "id": "uuid-note",
    "title": "Título",
    "content": "Contenido",
    "summary": null,
    "is_archived": false,
    "user_id": "uuid-user",
    "media_url": null,
    "created_at": "2026-02-19T10:00:00Z",
    "updated_at": "2026-02-19T10:00:00Z"
  }
]
```

> El listado no incluye `tags`, `tasks` ni `events` en ningún item.

### Reglas del listado
- Por defecto (`is_archived` no enviado o `false`): solo notas no archivadas.
- Con `is_archived=true`: solo notas archivadas.
- Ordenamiento por `updated_at` desc por defecto (más recientemente modificadas primero).
- Si se envía `limit`, se aplica como tope de resultados. Sin `limit`, se retornan todas.
- Para el **home**, el frontend manda `limit=3&sort_by=updated_at&order=desc` — no hay lógica especial en el backend.

---

### Obtener nota por ID
**GET** `/api/notes/{id}`

**Response (200 OK):**
```json
{
  "id": "uuid-note",
  "title": "Título",
  "content": "Contenido completo",
  "summary": "Resumen",
  "is_archived": false,
  "user_id": "uuid-user",
  "media_url": null,
  "created_at": "2026-02-19T10:00:00Z",
  "updated_at": "2026-02-19T10:00:00Z"
}
```

> Sin `tags`, `tasks` ni `events`. Para obtener las relaciones usar `/related`.

---

### Actualizar nota
**PATCH** `/api/notes/{id}`

**Request (todos los campos opcionales):**
```json
{
  "title": "Nuevo título",
  "content": "Nuevo contenido",
  "summary": "Nuevo resumen",
  "is_archived": true
}
```

**Response (200 OK):** misma estructura que GET /api/notes/{id}.

---

### Actualizar resumen de nota
**PATCH** `/api/notes/{id}/summary`

**Request:**
```json
{
  "summary": "Nuevo resumen"
}
```
o
```json
{
  "summary": null
}
```

**Response (200 OK):** misma estructura que GET /api/notes/{id}`.

> Si `summary` se envía como `null`, el campo se deja vacío (NULL) en la base de datos.

---

### Eliminar nota
**DELETE** `/api/notes/{id}`

**Response (204 No Content)**

---

### Obtener relaciones de una nota
**GET** `/api/notes/{id}/related`

**Response (200 OK):**
```json
{
  "tags": [
    { "id": "uuid-tag", "name": "Tag", "color": "#FF5733", "icon": "star" }
  ],
  "tasks": [
    { "id": "uuid-task", "title": "Tarea vinculada", "is_completed": false }
  ],
  "events": [
    { "id": "uuid-event", "title": "Evento vinculado", "start_time": "2026-02-20T10:00:00Z" }
  ]
}
```

---

### Vincular etiqueta a nota
**POST** `/api/notes/{id}/tags`

**Request:**
```json
{ "tag_id": "uuid-tag" }
```

**Response (200 OK):**
```json
{ "message": "Etiqueta asignada correctamente", "assigned": 1 }
```

---

### Desvincular etiqueta de nota
**DELETE** `/api/notes/{id}/tags/{tag_id}`

**Response (204 No Content)**

---

## 2. Cambios respecto a la implementación anterior

Los siguientes cambios rompen la versión anterior del módulo y deben aplicarse juntos:

| Qué cambia | Antes | Después |
|---|---|---|
| `NoteResponse` en GET y POST | Incluía `tags`, `tasks`, `events` embebidos | Solo retorna campos base de la nota |
| Endpoint para vincular tags | `POST /api/notes/tags` con body `{note_id, tag_ids}` | `POST /api/notes/{note_id}/tags` con body `{tag_id}` |
| Endpoint nuevo | No existía | `GET /api/notes/{id}/related` |
| Vinculación con tasks/events | No existía en notas | Se maneja desde `/api/relations` |

## 3. Notas de implementación
- `NoteResponse` y `NoteCreate` responden sin relaciones embebidas. Eliminar los campos `tags`, `tasks` y `events` del schema `NoteResponse`.
- `GET /api/notes/{id}/related` consulta: `note_tags` → `tags`, `task_notes` → `tasks`, `event_notes` → `events`.
- El campo `summary` es opcional, puede ser llenado manualmente o por IA en el futuro.
- `media_url` es opcional, reservado para soporte futuro de archivos adjuntos.
