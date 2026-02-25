---
alwaysApply: false
scope: events
---

# Reglas de Events

Este documento define el funcionamiento del módulo de eventos, incluyendo reglas de filtrado, ordenamiento y contratos de request/response. Mantenerlo actualizado con cualquier cambio en `events/api.py` y `events/schemas.py`.

## 1. Estado y Arquitectura

El módulo de Eventos sigue la arquitectura estándar de separación:
1. `EventResponse` **solo** incluye sus campos propios, recordatorios vinculados (`reminders_data`), y las etiquetas vinculadas (`tags`).
2. Las relaciones **hacia** otras entidades principales (tareas, notas) no se embeben en la respuesta base. Se consultan a través de `/api/events/{id}/related`.
3. Todos los endpoints de vinculación entre eventos y (tareas/notas) viven en `relations/api.py`.

---

## 2. Endpoints Principales

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
  "tags": []
}
```

---

### Listar eventos
**GET** `/api/events/`

**Query params:**
- `start_date`: ISO 8601 — filtrar eventos desde esta fecha (inclusive)
- `end_date`: ISO 8601 — filtrar eventos hasta esta fecha (inclusive)

**Response (200 OK):** array de `EventResponse`. Todos los eventos retornados incluirán sus `tags` vinculadas embebidas en la respuesta, estructuradas como `[{"id": "...", "name": "...", "color": "...", "icon": "..."}]`.

**Reglas del listado:**
- Sin filtros: retorna todos los eventos del usuario, ordenados por `start_time` asc.
- Con `start_date` y/o `end_date`: filtra eventos cuyo `start_time` esté dentro del rango.
- No hay paginación cursor en eventos (a diferencia de Tasks). Se retornan todos los que coinciden.
- Para el **home**, el frontend manda `start_date=hoy&end_date=hoy+7días` — no hay lógica especial en el backend.

---

### Obtener evento por ID
**GET** `/api/events/{event_id}`

**Response (200 OK):** misma estructura que POST. Incluye la lista embebida de `tags`.

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

**Response (200 OK):** misma estructura que GET. Incluye sus `tags`.

> Si se envía `reminders`, reemplaza completamente los recordatorios existentes (mismo comportamiento que Tasks).

---

### Eliminar evento
**DELETE** `/api/events/{event_id}`

**Response (204 No Content)**

---

## 3. Endpoints de Relaciones (Related & Tags)

### Obtener relaciones cruzadas de un evento
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

## 4. Tabla de base de datos utilizada

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

## 5. Notas de implementación
- `reminders` en eventos sigue exactamente el mismo patrón que en Tasks: `remind_at = start_time - offset`.
- `has_reminder` se actualiza automáticamente al crear/modificar recordatorios.
- El backend debe validar que `end_time > start_time`.