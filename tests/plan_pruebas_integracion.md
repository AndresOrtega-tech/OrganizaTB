# Plan: Tests de Integración — OrganizaT API

> **Objetivo:** Probar todos los endpoints de Tasks, Tags, Notes, Events, Relations y Reminders (excepto registro y cambio de contraseña), y al final eliminar todo lo creado.
>
> **Archivo:** `tests/test_integracion.py`
>
> **Variables de entorno requeridas (`.env`):**
> ```
> TEST_EMAIL=correo@ejemplo.com
> TEST_PASSWORD=contraseña123
> BASE_URL=https://api-organiza-tb.vercel.app/api
> ```

---

## Flujo secuencial de pruebas

### Fase 0 — Login (obtener token)

| Paso | Método | Endpoint | Body | Verificar |
|------|--------|----------|------|-----------|
| 0.1 | POST | `/api/auth/login` | `{"email": "$TEST_EMAIL", "password": "$TEST_PASSWORD"}` | status 200, `access_token` presente |

> El token se almacena en variable global y se usa en header `Authorization: Bearer <token>` para todas las llamadas siguientes.

---

### Fase 1 — Crear Tags (2 tags)

| Paso | Método | Endpoint | Body | Verificar |
|------|--------|----------|------|-----------|
| 1.1 | POST | `/api/tags/` | `{"name": "TestTag1_<ts>", "color": "#FF5733"}` | status 201, `id` presente, `name` correcto |
| 1.2 | POST | `/api/tags/` | `{"name": "TestTag2_<ts>", "color": "#33FF57"}` | status 201, `id` presente, `name` correcto |

> **IDs guardados:** `tag1_id`, `tag2_id`
> `<ts>` = timestamp para evitar colisiones en re-ejecuciones.

---

### Fase 2 — Crear Tasks (2 tareas)

| Paso | Método | Endpoint | Body | Verificar |
|------|--------|----------|------|-----------|
| 2.1 | POST | `/api/tasks/` | `{"title": "Tarea con reminder", "description": "Desc test", "due_date": "<now+2h ISO>", "priority": "alta", "reminders": [{"value": 30, "unit": "minutes"}]}` | status 201, `id`, `title`, `priority`=="alta", `reminders_data` con 1 elemento, `has_reminder`==true |
| 2.2 | POST | `/api/tasks/` | `{"title": "Tarea sin reminder", "description": "Desc 2", "due_date": "<now+3h ISO>", "priority": "baja"}` | status 201, `id`, `has_reminder`==false, `reminders_data`==[] |

> **IDs guardados:** `task1_id` (con reminder), `task2_id` (sin reminder)
> **IDs de reminders guardados:** `reminder1_id` (del task1)

---

### Fase 3 — Crear Notes (2 notas)

| Paso | Método | Endpoint | Body | Verificar |
|------|--------|----------|------|-----------|
| 3.1 | POST | `/api/notes/` | `{"title": "Nota test 1", "content": "Contenido de prueba", "summary": "Resumen 1"}` | status 201, `id`, `title`=="Nota test 1" |
| 3.2 | POST | `/api/notes/` | `{"title": "Nota test 2", "content": "Contenido 2"}` | status 201, `id` |

> **IDs guardados:** `note1_id`, `note2_id`

---

### Fase 4 — Crear Events (2 eventos)

| Paso | Método | Endpoint | Body | Verificar |
|------|--------|----------|------|-----------|
| 4.1 | POST | `/api/events/` | `{"title": "Evento con reminder", "description": "Evento test", "start_time": "<now+1h ISO>", "end_time": "<now+2h ISO>", "location": "Oficina", "reminders": [{"value": 15, "unit": "minutes"}]}` | status 201, `id`, `title`, `has_reminder`==true |
| 4.2 | POST | `/api/events/` | `{"title": "Evento sin reminder", "start_time": "<now+4h ISO>", "end_time": "<now+5h ISO>"}` | status 201, `id`, `has_reminder`==false |

> **IDs guardados:** `event1_id` (con reminder), `event2_id` (sin reminder)

---

### Fase 5 — GET Listas (todos los endpoints)

| Paso | Método | Endpoint | Query params | Verificar |
|------|--------|----------|--------------|-----------|
| 5.1 | GET | `/api/tags/` | — | status 200, lista con al menos 2 tags |
| 5.2 | GET | `/api/tasks/` | `?view=tasks&tab=pending` | status 200, `data` con al menos 2 tasks, `has_more` presente |
| 5.3 | GET | `/api/tasks/` | `?view=tasks&tab=pending&priority=alta` | status 200, solo tasks con priority=="alta" |
| 5.4 | GET | `/api/notes/` | `?is_archived=false` | status 200, lista con al menos 2 notes |
| 5.5 | GET | `/api/events/` | — | status 200, lista con al menos 2 events |
| 5.6 | GET | `/api/reminders/` | `?status=pending` | status 200, al menos 1 reminder |

---

### Fase 6 — GET Individuales (por ID)

| Paso | Método | Endpoint | Verificar |
|------|--------|----------|-----------|
| 6.1 | GET | `/api/tasks/{task1_id}` | status 200, `id`==task1_id, `title` correcto |
| 6.2 | GET | `/api/notes/{note1_id}` | status 200, `id`==note1_id |
| 6.3 | GET | `/api/events/{event1_id}` | status 200, `id`==event1_id |

---

### Fase 7 — PATCH / Actualizar entidades

| Paso | Método | Endpoint | Body | Verificar |
|------|--------|----------|------|-----------|
| 7.1 | PATCH | `/api/tags/{tag1_id}` | `{"name": "TestTag1 Updated", "color": "#000000"}` | status 200, `name`=="TestTag1 Updated" |
| 7.2 | PATCH | `/api/tasks/{task1_id}` | `{"title": "Tarea actualizada", "is_completed": true}` | status 200, `is_completed`==true |
| 7.3 | PATCH | `/api/notes/{note1_id}` | `{"title": "Nota actualizada", "content": "Contenido nuevo"}` | status 200, `title`=="Nota actualizada" |
| 7.4 | PATCH | `/api/notes/{note1_id}/summary` | `{"summary": "Resumen actualizado"}` | status 200, `summary`=="Resumen actualizado" |
| 7.5 | PATCH | `/api/events/{event1_id}` | `{"title": "Evento actualizado", "location": "Casa"}` | status 200, `title`=="Evento actualizado" |
| 7.6 | PATCH | `/api/reminders/{reminder1_id}` | `{"status": "sent"}` | status 200, `status`=="sent" |

---

### Fase 8 — Asignar Tags a entidades

| Paso | Método | Endpoint | Body | Verificar |
|------|--------|----------|------|-----------|
| 8.1 | POST | `/api/tasks/{task1_id}/tags` | `{"tag_id": "$tag1_id"}` | status 200, `assigned`==1 |
| 8.2 | POST | `/api/tasks/{task1_id}/tags` | `{"tag_id": "$tag2_id"}` | status 200, `assigned`==1 |
| 8.3 | POST | `/api/notes/{note1_id}/tags` | `{"tag_id": "$tag1_id"}` | status 200, `assigned`==1 |
| 8.4 | POST | `/api/events/{event1_id}/tags` | `{"tag_id": "$tag1_id"}` | status 200, `assigned`==1 |

---

### Fase 9 — GET Related (entidades relacionadas, pre-relations)

| Paso | Método | Endpoint | Verificar |
|------|--------|----------|-----------|
| 9.1 | GET | `/api/tasks/{task1_id}/related` | status 200, `tags` con al menos 1 tag |
| 9.2 | GET | `/api/notes/{note1_id}/related` | status 200, `tags` con al menos 1 tag |
| 9.3 | GET | `/api/events/{event1_id}/related` | status 200, `tags` con al menos 1 tag |

---

### Fase 10 — Crear Relations (vinculaciones)

| Paso | Método | Endpoint | Body | Verificar |
|------|--------|----------|------|-----------|
| 10.1 | POST | `/api/relations/task-note` | `{"task_id": "$task1_id", "note_id": "$note1_id"}` | status 201, `message` presente |
| 10.2 | POST | `/api/relations/task-event` | `{"task_id": "$task1_id", "event_id": "$event1_id"}` | status 201, `message` presente |
| 10.3 | POST | `/api/relations/note-event` | `{"note_id": "$note1_id", "event_id": "$event1_id"}` | status 201, `message` presente |

---

### Fase 11 — Verificar Relations (GET related post-vinculación)

| Paso | Método | Endpoint | Verificar |
|------|--------|----------|-----------|
| 11.1 | GET | `/api/tasks/{task1_id}/related` | status 200, `notes` con note1, `events` con event1 |
| 11.2 | GET | `/api/notes/{note1_id}/related` | status 200, `tasks` con task1, `events` con event1 |
| 11.3 | GET | `/api/events/{event1_id}/related` | status 200, `tasks` con task1, `notes` con note1 |

---

### Fase 12 — Remover Tags de entidades

| Paso | Método | Endpoint | Verificar |
|------|--------|----------|-----------|
| 12.1 | DELETE | `/api/tasks/{task1_id}/tags/{tag1_id}` | status 204 |
| 12.2 | DELETE | `/api/notes/{note1_id}/tags/{tag1_id}` | status 204 |
| 12.3 | DELETE | `/api/events/{event1_id}/tags/{tag1_id}` | status 204 |

---

### Fase 13 — Eliminar Relations

| Paso | Método | Endpoint | Body | Verificar |
|------|--------|----------|------|-----------|
| 13.1 | DELETE | `/api/relations/task-note` | `{"task_id": "$task1_id", "note_id": "$note1_id"}` | status 200 |
| 13.2 | DELETE | `/api/relations/task-event` | `{"task_id": "$task1_id", "event_id": "$event1_id"}` | status 200 |
| 13.3 | DELETE | `/api/relations/note-event` | `{"note_id": "$note1_id", "event_id": "$event1_id"}` | status 200 |

---

### Fase 14 — Eliminar Reminders

| Paso | Método | Endpoint | Verificar |
|------|--------|----------|-----------|
| 14.1 | DELETE | `/api/reminders/{reminder1_id}` | status 204 |

---

### Fase 15 — Eliminar Tasks

| Paso | Método | Endpoint | Verificar |
|------|--------|----------|-----------|
| 15.1 | DELETE | `/api/tasks/{task1_id}` | status 204 |
| 15.2 | DELETE | `/api/tasks/{task2_id}` | status 204 |

---

### Fase 16 — Eliminar Notes

| Paso | Método | Endpoint | Verificar |
|------|--------|----------|-----------|
| 16.1 | DELETE | `/api/notes/{note1_id}` | status 204 |
| 16.2 | DELETE | `/api/notes/{note2_id}` | status 204 |

---

### Fase 17 — Eliminar Events

| Paso | Método | Endpoint | Verificar |
|------|--------|----------|-----------|
| 17.1 | DELETE | `/api/events/{event1_id}` | status 204 |
| 17.2 | DELETE | `/api/events/{event2_id}` | status 204 |

---

### Fase 18 — Eliminar Tags (último, porque FK dependen de ellos)

| Paso | Método | Endpoint | Verificar |
|------|--------|----------|-----------|
| 18.1 | DELETE | `/api/tags/{tag1_id}` | status 204 |
| 18.2 | DELETE | `/api/tags/{tag2_id}` | status 204 |

---

## Estructura del código

```
tests/
├── test_integracion.py              ← NUEVO (este test)
├── plan_pruebas_integracion.md      ← ESTE ARCHIVO
├── pruebas_estres_v1.py             (existente)
├── pruebas_limite_v1.py             (existente)
└── pruebas_limite_write_v1.py       (existente)
```

### Convenciones del código

- **Librería HTTP:** `aiohttp` (consistencia con tests existentes) + `asyncio`
- **Variables de entorno:** `os.environ` con `TEST_EMAIL`, `TEST_PASSWORD`, `BASE_URL`
- **Colores en terminal:** ANSI codes (verde=OK, rojo=FAIL, amarillo=INFO)
- **IDs creados:** almacenados en dict global para cleanup
- **Cada fase:** función async separada con prints de progreso
- **Resumen final:** total OK/FAIL/ERROR con detalle
- **Cleanup automático** si algo falla a mitad de camino

### Notas técnicas importantes

1. **DELETE de relations acepta body:** Usar `session.delete(url, json=body, headers=...)` (no es GET, es DELETE con body JSON)
2. **Reminders se crean automáticamente** al crear tasks/events con `reminders` field; no se crean manualmente
3. **Tag uniqueness por usuario:** Cada tag name es único por usuario; se usa sufijo timestamp para evitar colisiones
4. **Task list response es paginada:** `{"data": [...], "next_cursor": ..., "has_more": ...}`
5. **Notes list response es array directo:** `[...]` (sin paginación)
6. **Events list response es array directo:** `[...]` (sin paginación)
7. **Notes PATCH /summary** es un endpoint separado del PATCH normal de notes
8. **Reminder PATCH** puede actualizar `status` o `remind_at` individualmente

### Orden de eliminación (cleanup)

```
1. DELETE relations (task-note, task-event, note-event)
2. DELETE reminders
3. DELETE tasks (cascade elimina task_tags, task_notes, event_tasks)
4. DELETE notes (cascade elimina note_tags, task_notes, event_notes)
5. DELETE events (cascade elimina event_tags, event_tasks, event_notes)
6. DELETE tags (ya sin dependencias)
```

> Nota: Aunque Supabase tiene cascade deletes, el test elimina explícitamente en orden inverso para ser explícito y no depender del cascade.

---

## Total de endpoints probados

| Módulo | Endpoints | Total requests |
|--------|-----------|----------------|
| Auth | login | 1 |
| Tags | POST, GET, PATCH, DELETE | 8 |
| Tasks | POST, GET, GET(filter), GET(id), GET(related), PATCH, DELETE, POST(tags), DELETE(tags) | 13 |
| Notes | POST, GET, GET(id), GET(related), PATCH, PATCH(summary), DELETE, POST(tags), DELETE(tags) | 11 |
| Events | POST, GET, GET(id), GET(related), PATCH, DELETE, POST(tags), DELETE(tags) | 10 |
| Relations | POST (×3), DELETE (×3) | 6 |
| Reminders | GET, PATCH, DELETE | 3 |
| **TOTAL** | | **~52 requests** |
