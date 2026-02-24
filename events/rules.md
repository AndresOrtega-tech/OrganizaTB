---
alwaysApply: false
scope: events
---

# Reglas de Events

Este documento define el funcionamiento del módulo de eventos, incluyendo reglas de filtrado, ordenamiento y contratos de request/response. Mantenerlo actualizado con cualquier cambio en `events/api.py` y `events/schemas.py`.

## 1. Estado actual y deuda técnica pendiente

El módulo de eventos está en un estado intermedio de refactorización. Actualmente `EventResponse` embebe `tasks` y `notes` directamente, igual que lo hacía `NoteResponse` antes de ser refactorizado. La migración pendiente es:

| Qué cambiar | Estado actual | Estado objetivo |
|---|---|---|
| `EventResponse` embebe `tasks` y `notes` | Sí | Solo campos base |
| Endpoints de vinculación task/note en Events | Existen en `/api/events/tasks` y `/api/events/notes` | Migrar a `/api/relations` |
| `GET /api/events/{id}/related` | No existe aún | Implementar (mismo patrón que Tasks y Notes) |
| Vinculación de tags en Events | No existe aún | `POST /api/events/{id}/tags` + `DELETE /api/events/{id}/tags/{tag_id}` |

Hasta que se complete la migración, los endpoints de vinculación en Events siguen funcionando. Una vez migrados a Relations, quedan **deprecados**.

---

## 2. Endpoints (Events)

### Crear evento
**POST** `/api/events/`

**Request:**
```json
{
  "title": "Título del evento",
  "description": "Descripción opcional",
  "start_time": "2026-02-20T10:00:00Z",
  "end_time": "2026-02-20T11:00:00Z",
  "location": "Ubicación opcional",
  "is_all_day": false,
  "reminders": [
    { "unit": "minutes", "value": 30 }
  ]
}
```

**Response (201 Created):**
```json
{
  "id": "uuid-event",
  "title": "Título del evento",
  "description": "Descripción opcional",
  "start_time": "2026-02-20T10:00:00Z",
  "end_time": "2026-02-20T11:00:00Z",
  "location": "Ubicación opcional",
  "is_all_day": false,
  "user_id": "uuid-user",
  "created_at": "2026-02-19T10:00:00Z",
  "updated_at": "2026-02-19T10:00:00Z",
  "has_reminder": true,
  "reminders_data": [
    { "id": "uuid-reminder", "remind_at": "2026-02-20T09:30:00Z", "status": "pending" }
  ],
  "tasks": [],
  "notes": []
}
```

> `tasks` y `notes` se retornan vacíos en la creación. Esto cambiará cuando `EventResponse` sea refactorizado para no embeber relaciones (igual que se hizo con Notes).

---

### Listar eventos
**GET** `/api/events/`

**Query params:**
- `start_date`: ISO 8601 — filtrar eventos desde esta fecha (inclusive)
- `end_date`: ISO 8601 — filtrar eventos hasta esta fecha (inclusive)

**Response (200 OK):** array de `EventResponse`.

### Reglas del listado
- Sin filtros: retorna todos los eventos del usuario, ordenados por `start_time` asc.
- Con `start_date` y/o `end_date`: filtra eventos cuyo `start_time` esté dentro del rango.
- No hay paginación cursor en eventos (a diferencia de Tasks). Se retornan todos los que coinciden.
- Para el **home**, el frontend manda `start_date=hoy&end_date=hoy+7días` — no hay lógica especial en el backend.

---

### Obtener evento por ID
**GET** `/api/events/{event_id}`

**Response (200 OK):** misma estructura que POST.

---

### Actualizar evento
**PATCH** `/api/events/{event_id}`

**Request (todos los campos opcionales):**
```json
{
  "title": "Nuevo título",
  "description": "Nueva descripción",
  "start_time": "2026-02-21T10:00:00Z",
  "end_time": "2026-02-21T11:00:00Z",
  "location": "Nueva ubicación",
  "is_all_day": false,
  "reminders": [{ "unit": "hours", "value": 1 }]
}
```

**Response (200 OK):** misma estructura que GET.

> Si se envía `reminders`, reemplaza completamente los recordatorios existentes (mismo comportamiento que Tasks).

---

### Eliminar evento
**DELETE** `/api/events/{event_id}`

**Response (204 No Content)**

---

## 3. Endpoints de vinculación (pendientes de migración a Relations)

Estos endpoints existen actualmente en el módulo de Events pero serán deprecados y reemplazados por `/api/relations`. Se documentan aquí temporalmente.

| Endpoint actual (deprecado) | Reemplazado por |
|---|---|
| `POST /api/events/tasks` | `POST /api/relations/task-event` |
| `DELETE /api/events/{event_id}/tasks/{task_id}` | `DELETE /api/relations/task-event` |
| `POST /api/events/notes` | `POST /api/relations/note-event` |
| `DELETE /api/events/{event_id}/notes/{note_id}` | `DELETE /api/relations/note-event` |

---

## 4. Endpoints pendientes de implementación

### Obtener relaciones de un evento
**GET** `/api/events/{event_id}/related`

**Response esperada (200 OK):**
```json
{
  "tags": [
    { "id": "uuid-tag", "name": "Tag", "color": "#FF5733", "icon": "star" }
  ],
  "tasks": [
    { "id": "uuid-task", "title": "Tarea vinculada", "is_completed": false }
  ],
  "notes": [
    { "id": "uuid-note", "title": "Nota vinculada" }
  ]
}
```

> Mismo patrón que `GET /api/tasks/{id}/related` y `GET /api/notes/{id}/related`. Consulta: `event_tags` → `tags`, `event_tasks` → `tasks`, `event_notes` → `notes`.

---

### Vincular etiqueta a evento
**POST** `/api/events/{event_id}/tags`

**Request:**
```json
{ "tag_id": "uuid-tag" }
```

**Response (200 OK):**
```json
{ "message": "Etiqueta asignada correctamente", "assigned": 1 }
```

---

### Desvincular etiqueta de evento
**DELETE** `/api/events/{event_id}/tags/{tag_id}`

**Response (204 No Content)**

---

## 5. Tabla de base de datos utilizada

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | Generado automáticamente |
| `user_id` | UUID | Referencia al usuario propietario |
| `title` | TEXT | Requerido |
| `description` | TEXT | Opcional, máx. 500 caracteres |
| `start_time` | TIMESTAMPTZ | Requerido |
| `end_time` | TIMESTAMPTZ | Requerido |
| `location` | TEXT | Opcional |
| `is_all_day` | BOOLEAN | Default false |
| `has_reminder` | BOOLEAN | Default false |
| `created_at` / `updated_at` | TIMESTAMPTZ | Automáticos |

Las relaciones con tareas y notas se almacenan en `event_tasks` y `event_notes`. Las etiquetas en `event_tags`.

## 6. Notas de implementación
- `reminders` en eventos sigue exactamente el mismo patrón que en Tasks: `remind_at = start_time - offset`.
- `has_reminder` se actualiza automáticamente al crear/modificar recordatorios.
- El backend debe validar que `end_time > start_time`.
- La migración completa de este módulo sigue el mismo proceso que se hizo con Notes: limpiar `EventResponse`, crear `/related`, mover vinculaciones a Relations.