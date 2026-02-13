# Contratos de API (Ejemplos de Request/Response)

Este documento sirve como referencia de los formatos JSON esperados para las peticiones y respuestas de la API. Los ejemplos están basados en pruebas de integración reales.

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
