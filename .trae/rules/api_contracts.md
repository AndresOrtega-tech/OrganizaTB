# Contratos de API (Ejemplos de Request/Response)

Este documento sirve como referencia de los formatos JSON esperados para las peticiones y respuestas de la API. Los ejemplos están basados en pruebas de integración reales.

## 0. Autenticación (Auth)

### Renovar Token (Refresh Token)
**POST** `/api/auth/refresh`

**Request:**
```json
{
  "refresh_token": "J9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6In..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "refresh_token": "J9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6In...",
  "expires_in": 3600,
  "user": {
    "email": "usuario@ejemplo.com",
    "full_name": "Juan Perez",
    "avatar": "https://..."
  }
}
```

---

## 1. Etiquetas (Tags)

### Crear Etiqueta
**POST** `/api/tags/`

**Request:**
```json
{
  "name": "TestTag_23ea2a",
  "color": "#FF5733"
}
```

**Response (201 Created):**
```json
{
  "name": "TestTag_23ea2a",
  "color": "#FF5733",
  "id": "f92ec9e7-82ec-4279-9d58-428c57393413",
  "user_id": "be22a2c3-67f3-4756-a9c6-956a015cb4ea",
  "icon": null,
  "created_at": "2026-02-07T21:35:25.736383+00:00"
}
```

---

## 2. Tareas (Tasks)

### Crear Tarea con Recordatorios
**POST** `/api/tasks/`

**Request:**
```json
{
  "title": "Integration Test Task",
  "description": "Testing full flow",
  "priority": "alta",
  "due_date": "2026-02-08T21:35:25.777257+00:00",
  "reminders": [
    {
      "unit": "minutes",
      "value": 30
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "title": "Integration Test Task",
  "description": "Testing full flow",
  "due_date": "2026-02-08T21:35:25.777257Z",
  "is_completed": false,
  "priority": "alta",
  "id": "013e0fc6-c127-435e-8821-b883774dc19d",
  "user_id": "be22a2c3-67f3-4756-a9c6-956a015cb4ea",
  "created_at": "2026-02-07T21:35:26.018687Z",
  "updated_at": "2026-02-07T21:35:26.018687Z",
  "tags": [],
  "notes": [],
  "events": [],
  "reminders_data": [
    {
      "id": "5812d754-c6a4-44e2-a42b-f77afa9a2c0c",
      "remind_at": "2026-02-08T21:05:25.777257Z",
      "status": "pending"
    }
  ],
  "has_reminder": true
}
```

### Vincular Tarea a Nota
**POST** `/api/tasks/notes`

**Request:**
```json
{
  "task_id": "013e0fc6-c127-435e-8821-b883774dc19d",
  "note_id": "a8efc7c2-d053-43e3-b77f-699ac91c01c5"
}
```

**Response (201 Created):**
```json
{
  "message": "Nota vinculada a la tarea exitosamente"
}
```

### Vincular Tarea a Etiqueta
**POST** `/api/tasks/tags`

**Request:**
```json
{
  "task_id": "013e0fc6-c127-435e-8821-b883774dc19d",
  "tag_ids": [
    "f92ec9e7-82ec-4279-9d58-428c57393413"
  ]
}
```

**Response (200 OK):**
```json
{
  "message": "Etiquetas asignadas correctamente",
  "assigned_count": 1
}
```

### Listar Tareas (Paginado con cursor)
**GET** `/api/tasks/`

**Query params:**
| Param | Tipo | Default | Descripción |
|-------|------|---------|-------------|
| `view` | `home` \| `tasks` | — | Filtrado inteligente por vista |
| `limit` | int (1–50) | `10` | Items por página |
| `cursor` | string (ISO 8601) | — | `due_date` del último item recibido |
| `is_completed` | bool | — | Ignorado si se usa `view` |
| `priority` | `baja`\|`media`\|`alta` | — | Filtro de prioridad |
| `tag_ids` | string[] | — | AND: tarea debe tener TODOS los tags |
| `start_date` / `end_date` | datetime | — | Rango de fechas |
| `date_field` | `due_date`\|`updated_at`\|`created_at` | `due_date` | Campo del rango |
| `sort_by` | `updated_at`\|`due_date`\|`priority` | `updated_at` | Ignorado si `view` o `cursor` |
| `order` | `asc`\|`desc` | `desc` | Ignorado si `view` o `cursor` |

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "013e0fc6-c127-435e-8821-b883774dc19d",
      "title": "Entregar informe",
      "due_date": "2026-02-20T10:00:00+00:00",
      "is_completed": false,
      "priority": "alta",
      "tags": [],
      "notes": [],
      "events": [],
      "reminders_data": [],
      "has_reminder": false
    }
  ],
  "next_cursor": "2026-02-20T10:00:00+00:00",
  "has_more": true
}
```
> `next_cursor` es `null` cuando no hay más páginas o el último item no tiene `due_date`.

---

### Obtener Tarea (Con relaciones completas)
**GET** `/api/tasks/{id}`

**Response (200 OK):**
```json
{
  "title": "Integration Test Task",
  "description": "Testing full flow",
  "due_date": "2026-02-08T21:35:25.777257Z",
  "is_completed": false,
  "priority": "alta",
  "id": "013e0fc6-c127-435e-8821-b883774dc19d",
  "tags": [
    {
      "name": "TestTag_23ea2a",
      "color": "#FF5733",
      "id": "f92ec9e7-82ec-4279-9d58-428c57393413"
    }
  ],
  "notes": [
    {
      "id": "a8efc7c2-d053-43e3-b77f-699ac91c01c5",
      "title": "Test Note"
    }
  ],
  "events": [
    {
      "id": "7469c3b7-5c25-4b09-a7e9-0491fed14beb",
      "title": "Test Event",
      "start_time": "2026-02-09T21:35:26.478948Z"
    }
  ],
  "reminders_data": [
    {
      "id": "5812d754-c6a4-44e2-a42b-f77afa9a2c0c",
      "remind_at": "2026-02-08T21:05:25.777257Z",
      "status": "pending"
    }
  ],
  "has_reminder": true
}
```

### Obtener relaciones de una tarea (notas y eventos)
**GET** `/api/tasks/{id}/related`

**Response (200 OK):**
```json
{
  "notes": [
    { "id": "a8efc7c2-...", "title": "Nota de reunión", "content": "..." }
  ],
  "events": [
    { "id": "7469c3b7-...", "title": "Reunión Q1", "start_time": "2026-02-20T10:00:00Z" }
  ]
}
```
> Usar solo para sincronizar relaciones tras un optimistic update fallido. Para el detalle completo, usar `GET /api/tasks/{id}`.

---

## 3. Notas (Notes)

### Crear Nota
**POST** `/api/notes/`

**Request:**
```json
{
  "title": "Test Note",
  "content": "Linked note content"
}
```

**Response (201 Created):**
```json
{
  "title": "Test Note",
  "content": "Linked note content",
  "summary": null,
  "is_archived": false,
  "id": "a8efc7c2-d053-43e3-b77f-699ac91c01c5",
  "user_id": "be22a2c3-67f3-4756-a9c6-956a015cb4ea",
  "created_at": "2026-02-07T21:35:26.434172Z",
  "tags": [],
  "tasks": [],
  "events": []
}
```

### Obtener Nota (Con relaciones)
**GET** `/api/notes/{id}`

**Response (200 OK):**
```json
{
  "title": "Test Note",
  "content": "Linked note content",
  "id": "a8efc7c2-d053-43e3-b77f-699ac91c01c5",
  "tags": [
    {
      "name": "TestTag_23ea2a",
      "color": "#FF5733",
      "id": "f92ec9e7-82ec-4279-9d58-428c57393413"
    }
  ],
  "tasks": [
    {
      "id": "013e0fc6-c127-435e-8821-b883774dc19d",
      "title": "Integration Test Task",
      "is_completed": false
    }
  ],
  "events": [
    {
      "id": "7469c3b7-5c25-4b09-a7e9-0491fed14beb",
      "title": "Test Event",
      "start_time": "2026-02-09T21:35:26.478948Z"
    }
  ]
}
```

---

## 4. Eventos (Events)

### Crear Evento
**POST** `/api/events/`

**Request:**
```json
{
  "title": "Test Event",
  "start_time": "2026-02-09T21:35:26.478948+00:00",
  "end_time": "2026-02-09T22:35:26.478960+00:00"
}
```

**Response (201 Created):**
```json
{
  "title": "Test Event",
  "start_time": "2026-02-09T21:35:26.478948Z",
  "end_time": "2026-02-09T22:35:26.478960Z",
  "is_all_day": false,
  "id": "7469c3b7-5c25-4b09-a7e9-0491fed14beb",
  "user_id": "be22a2c3-67f3-4756-a9c6-956a015cb4ea",
  "reminders_data": [],
  "tasks": [],
  "notes": [],
  "has_reminder": false
}
```

### Vincular Evento a Tarea
**POST** `/api/events/tasks`

**Request:**
```json
{
  "event_id": "7469c3b7-5c25-4b09-a7e9-0491fed14beb",
  "task_id": "013e0fc6-c127-435e-8821-b883774dc19d"
}
```

**Response (201 Created):**
```json
{
  "message": "Vinculado correctamente"
}
```

### Vincular Evento a Etiqueta
**POST** `/api/events/tags`

**Request:**
```json
{
  "event_id": "7469c3b7-5c25-4b09-a7e9-0491fed14beb",
  "tag_ids": [
    "f92ec9e7-82ec-4279-9d58-428c57393413"
  ]
}
```

**Response (200 OK):**
```json
{
  "message": "Etiquetas asignadas correctamente",
  "assigned_count": 1
}
```

### Obtener Evento (Con relaciones)
**GET** `/api/events/{id}`

**Response (200 OK):**
```json
{
  "title": "Test Event",
  "start_time": "2026-02-09T21:35:26.478948Z",
  "end_time": "2026-02-09T22:35:26.478960Z",
  "id": "7469c3b7-5c25-4b09-a7e9-0491fed14beb",
  "tags": [
    {
      "name": "TestTag_23ea2a",
      "color": "#FF5733",
      "id": "f92ec9e7-82ec-4279-9d58-428c57393413"
    }
  ],
  "tasks": [
    {
      "id": "013e0fc6-c127-435e-8821-b883774dc19d",
      "title": "Integration Test Task",
      "is_completed": false
    }
  ],
  "notes": [
    {
      "id": "a8efc7c2-d053-43e3-b77f-699ac91c01c5",
      "title": "Test Note"
    }
  ],
  "has_reminder": false
}
```
