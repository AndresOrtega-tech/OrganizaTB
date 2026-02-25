# Plan de Implementación — Refactorización del Módulo Events

---

## Contexto

Events es el único módulo que no completó la migración al patrón establecido durante la refactorización de Tasks y Notes. Los problemas actuales son:

- `EventResponse` embebe `tasks` y `notes` directamente en el response base
- Los endpoints de vinculación (`/tasks`, `/notes`) viven dentro de Events en lugar de en Relations
- No existe el endpoint `GET /events/{id}/related`
- No existe soporte de etiquetas (`/events/{id}/tags`)
- `TagUpdate` no acepta el campo `icon` aunque existe en BD y en `TagResponse`

---

## Estado actual vs. Estado objetivo

| Aspecto | Estado Actual | Estado Objetivo |
|---|---|---|
| `EventResponse` | Incluye `tasks` y `notes` embebidos | Solo campos base del evento |
| Vinculación tasks/notes | Vive en `/api/events/tasks` y `/api/events/notes` | Solo en `/api/relations` (ya existe) |
| `GET /events/{id}/related` | No existe | Implementado — retorna `tags`, `tasks` y `notes` |
| Etiquetas en eventos | No existe | `POST` y `DELETE /events/{id}/tags` |
| `TagUpdate` (icon) | No acepta `icon` | Campo `icon` agregado |

---

## Archivos involucrados

| Archivo | Acción | Descripción |
|---|---|---|
| `events/schemas.py` | MODIFICAR | Limpiar `EventResponse`, agregar `EventRelatedResponse` y `EventAssignTag` |
| `events/api.py` | MODIFICAR | Limpiar queries, eliminar 4 endpoints de vinculación, agregar `/related` y `/tags` |
| `tags/schemas.py` | MODIFICAR | Agregar campo `icon` a `TagUpdate` |

---

## Resumen de pasos

| Paso | Archivo | Qué hacer | Tipo |
|---|---|---|---|
| 1 | `events/schemas.py` | Quitar `tasks` y `notes` de `EventResponse` | ELIMINAR |
| 2 | `events/schemas.py` | Agregar `EventRelatedResponse` con `tags`, `tasks` y `notes` | AGREGAR |
| 3 | `events/schemas.py` | Agregar `EventAssignTag` con campo `tag_id` | AGREGAR |
| 4 | `events/api.py` | Limpiar SELECT de `list_events` (quitar joins de tasks/notes) | MODIFICAR |
| 5 | `events/api.py` | Limpiar SELECT de `get_event` (quitar joins de tasks/notes) | MODIFICAR |
| 6 | `events/api.py` | Limpiar `update_event` (quitar procesamiento de tasks/notes en response) | MODIFICAR |
| 7 | `events/api.py` | Eliminar `POST /tasks` (`link_task`) | ELIMINAR |
| 8 | `events/api.py` | Eliminar `DELETE /{id}/tasks/{task_id}` (`unlink_task`) | ELIMINAR |
| 9 | `events/api.py` | Eliminar `POST /notes` (`link_note`) | ELIMINAR |
| 10 | `events/api.py` | Eliminar `DELETE /{id}/notes/{note_id}` (`unlink_note`) | ELIMINAR |
| 11 | `events/api.py` | Agregar `GET /{event_id}/related` | NUEVO |
| 12 | `events/api.py` | Agregar `POST /{event_id}/tags` | NUEVO |
| 13 | `events/api.py` | Agregar `DELETE /{event_id}/tags/{tag_id}` | NUEVO |
| 14 | `tags/schemas.py` | Agregar `icon: Optional[str]` a `TagUpdate` | MODIFICAR |
| 15 | `tags/api.py` | Verificar que PATCH pasa `icon` a la BD si viene en el body | VERIFICAR |

---

## Detalle técnico por paso

### PASO 1 — Quitar `tasks` y `notes` de `EventResponse`

**Archivo:** `events/schemas.py`

Eliminar los dos campos del modelo. El response base del evento solo debe retornar sus campos propios.

```python
# ANTES — EventResponse incluye:
tasks: List[TaskSummary] = []
notes: List[NoteSummary] = []

# DESPUÉS — eliminar ambas líneas completamente
```

`EventResponse` final debe quedar con: `id`, `user_id`, `title`, `description`, `start_time`, `end_time`, `location`, `is_all_day`, `has_reminder`, `reminders_data`, `created_at`, `updated_at`.

---

### PASO 2 — Agregar `EventRelatedResponse`

**Archivo:** `events/schemas.py`

Nuevo schema para el endpoint `/related`. Mismo patrón que `NoteRelatedResponse` y `TaskRelatedResponse`.

```python
class EventRelatedResponse(BaseModel):
    tags: List[TagResponse] = []
    tasks: List[TaskSummary] = []
    notes: List[NoteSummary] = []
```

> Importar `TagResponse` desde `tags/schemas.py` igual que lo hace el módulo de Notes.

---

### PASO 3 — Agregar `EventAssignTag`

**Archivo:** `events/schemas.py`

Schema para el body del endpoint `POST /{event_id}/tags`. Mismo patrón que `NoteAssignTag` y `TaskAssignTags`.

```python
class EventAssignTag(BaseModel):
    tag_id: str = Field(..., description="ID de la etiqueta a asignar al evento")
```

---

### PASO 4 — Limpiar SELECT de `list_events`

**Archivo:** `events/api.py`

```python
# ANTES
query = supabase.table("events") \
    .select("*, reminders(*), event_tasks(tasks(id, title, is_completed)), event_notes(notes(id, title))") \
    .eq("user_id", user.id)

# DESPUÉS
query = supabase.table("events") \
    .select("*, reminders(*)") \
    .eq("user_id", user.id)
```

También eliminar el bloque de procesamiento dentro del `for event in events` que construía `tasks_list` y `notes_list`:

```python
# ELIMINAR estos bloques del loop:
tasks_list = []
if "event_tasks" in event:
    for item in event["event_tasks"]:
        if item.get("tasks"):
            tasks_list.append(item["tasks"])
    del event["event_tasks"]
event["tasks"] = tasks_list

notes_list = []
if "event_notes" in event:
    for item in event["event_notes"]:
        if item.get("notes"):
            notes_list.append(item["notes"])
    del event["event_notes"]
event["notes"] = notes_list
```

---

### PASO 5 — Limpiar SELECT de `get_event`

**Archivo:** `events/api.py`

```python
# ANTES
res = supabase.table("events") \
    .select("*, reminders(*), event_tasks(tasks(id, title, is_completed)), event_notes(notes(id, title))") \
    .eq("id", event_id).eq("user_id", user.id)

# DESPUÉS
res = supabase.table("events") \
    .select("*, reminders(*)") \
    .eq("id", event_id).eq("user_id", user.id)
```

Eliminar también los bloques de procesamiento de `tasks_list` y `notes_list` al final de `get_event`, exactamente igual que en el paso 4.

---

### PASO 6 — Limpiar `update_event`

**Archivo:** `events/api.py`

`update_event` construye el response final con el evento actualizado + sus reminders. No toca `event_tasks` ni `event_notes`, así que solo hay que verificar que el `return` al final no intente incluir `tasks` o `notes`. Si el schema ya fue limpiado en el Paso 1, Pydantic no los va a incluir de todos modos, pero confirmar que no haya procesamiento manual residual.

---

### PASO 7 — Eliminar `POST /tasks` (`link_task`)

**Archivo:** `events/api.py`

Eliminar el endpoint completo:

```python
# ELIMINAR TODO este bloque:
@router.post("/tasks", status_code=201)
async def link_task(link: EventLinkTask, user=Depends(get_current_user)):
    ...
```

**Reemplazado por:** `POST /api/relations/task-event` (ya existe y funciona)

---

### PASO 8 — Eliminar `DELETE /{id}/tasks/{task_id}` (`unlink_task`)

**Archivo:** `events/api.py`

```python
# ELIMINAR TODO este bloque:
@router.delete("/{event_id}/tasks/{task_id}", status_code=204)
async def unlink_task(event_id: str, task_id: str, user=Depends(get_current_user)):
    ...
```

**Reemplazado por:** `DELETE /api/relations/task-event` (ya existe y funciona)

---

### PASO 9 — Eliminar `POST /notes` (`link_note`)

**Archivo:** `events/api.py`

```python
# ELIMINAR TODO este bloque:
@router.post("/notes", status_code=201)
async def link_note(link: EventLinkNote, user=Depends(get_current_user)):
    ...
```

**Reemplazado por:** `POST /api/relations/note-event` (ya existe y funciona)

---

### PASO 10 — Eliminar `DELETE /{id}/notes/{note_id}` (`unlink_note`)

**Archivo:** `events/api.py`

```python
# ELIMINAR TODO este bloque:
@router.delete("/{event_id}/notes/{note_id}", status_code=204)
async def unlink_note(event_id: str, note_id: str, user=Depends(get_current_user)):
    ...
```

**Reemplazado por:** `DELETE /api/relations/note-event` (ya existe y funciona)

---

### PASO 11 — Agregar `GET /{event_id}/related`

**Archivo:** `events/api.py`

Mismo patrón que `get_task_related` y `get_note_related`. Consulta las tres tablas de unión del evento.

```python
@router.get("/{event_id}/related", response_model=EventRelatedResponse)
async def get_event_related(event_id: str, user=Depends(get_current_user)):
    try:
        # 1. Verificar que el evento pertenece al usuario
        event_check = supabase.table("events").select("id") \
            .eq("id", event_id).eq("user_id", user.id).execute()
        if not event_check.data:
            raise HTTPException(status_code=404, detail="Evento no encontrado")

        # 2. Tags: event_tags → tags
        tags_res = supabase.table("event_tags") \
            .select("tags(id, name, color, icon)") \
            .eq("event_id", event_id).execute()
        tags = [item["tags"] for item in tags_res.data if item.get("tags")]

        # 3. Tasks: event_tasks → tasks
        tasks_res = supabase.table("event_tasks") \
            .select("tasks(id, title, is_completed)") \
            .eq("event_id", event_id).execute()
        tasks = [item["tasks"] for item in tasks_res.data if item.get("tasks")]

        # 4. Notes: event_notes → notes
        notes_res = supabase.table("event_notes") \
            .select("notes(id, title)") \
            .eq("event_id", event_id).execute()
        notes = [item["notes"] for item in notes_res.data if item.get("notes")]

        return EventRelatedResponse(tags=tags, tasks=tasks, notes=notes)

    except Exception as e:
        logger.error(f"Error obteniendo relaciones del evento: {e}")
        raise HTTPException(status_code=400, detail=str(e))
```

---

### PASO 12 — Agregar `POST /{event_id}/tags`

**Archivo:** `events/api.py`

```python
@router.post("/{event_id}/tags", status_code=200)
async def assign_tag_to_event(event_id: str, body: EventAssignTag, user=Depends(get_current_user)):
    try:
        # 1. Verificar que el evento pertenece al usuario
        event_check = supabase.table("events").select("id") \
            .eq("id", event_id).eq("user_id", user.id).execute()
        if not event_check.data:
            raise HTTPException(status_code=404, detail="Evento no encontrado")

        # 2. Verificar que el tag pertenece al usuario
        tag_check = supabase.table("tags").select("id") \
            .eq("id", body.tag_id).eq("user_id", user.id).execute()
        if not tag_check.data:
            raise HTTPException(status_code=404, detail="Etiqueta no encontrada")

        # 3. Insertar en event_tags
        supabase.table("event_tags").upsert(
            {"event_id": event_id, "tag_id": body.tag_id},
            ignore_duplicates=True
        ).execute()

        return {"message": "Etiqueta asignada correctamente", "assigned": 1}

    except Exception as e:
        logger.error(f"Error asignando etiqueta a evento: {e}")
        raise HTTPException(status_code=400, detail=str(e))
```

---

### PASO 13 — Agregar `DELETE /{event_id}/tags/{tag_id}`

**Archivo:** `events/api.py`

```python
@router.delete("/{event_id}/tags/{tag_id}", status_code=204)
async def remove_tag_from_event(event_id: str, tag_id: str, user=Depends(get_current_user)):
    try:
        # Verificar que el evento pertenece al usuario
        event_check = supabase.table("events").select("id") \
            .eq("id", event_id).eq("user_id", user.id).execute()
        if not event_check.data:
            raise HTTPException(status_code=404, detail="Evento no encontrado")

        # Eliminar de event_tags
        supabase.table("event_tags") \
            .delete() \
            .eq("event_id", event_id) \
            .eq("tag_id", tag_id) \
            .execute()

    except Exception as e:
        logger.error(f"Error desvinculando etiqueta de evento: {e}")
        raise HTTPException(status_code=400, detail=str(e))
```

---

### PASO 14 — Agregar `icon` a `TagUpdate`

**Archivo:** `tags/schemas.py`

```python
# ANTES
class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50, min_length=1)
    color: Optional[str] = Field(None)

# DESPUÉS
class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50, min_length=1)
    color: Optional[str] = Field(None)
    icon: Optional[str] = Field(None, description="Icono de la etiqueta")
```

---

### PASO 15 — Verificar `tags/api.py`

**Archivo:** `tags/api.py`

Verificar que el PATCH construye `update_data` de forma dinámica. Si ya usa el patrón de excluir `None`, `icon` se incluirá automáticamente sin cambios adicionales.

```python
# Patrón correcto — icon se incluye solo si viene en el body
update_data = {k: v for k, v in update.dict().items() if v is not None}
```

Si el PATCH tiene los campos hardcodeados en lugar de usar este patrón dinámico, ajustar para que también incluya `icon`.

---

## Imports a agregar en `events/api.py`

Al agregar los nuevos endpoints, verificar que los schemas nuevos estén importados:

```python
from events.schemas import (
    EventCreate, EventUpdate, EventResponse,
    EventRelatedResponse,  # NUEVO
    EventAssignTag,        # NUEVO
)
```

Y eliminar los imports que ya no se usen tras borrar los endpoints de vinculación:

```python
# ELIMINAR si ya no se usan en ningún otro lugar:
EventLinkTask
EventLinkNote
```

---

## Tabla de endpoints: antes vs. después

### Endpoints que desaparecen

| Método | Endpoint | Motivo |
|---|---|---|
| POST | `/api/events/tasks` | Ya existe en `/api/relations/task-event` |
| DELETE | `/api/events/{id}/tasks/{task_id}` | Ya existe en `/api/relations/task-event` |
| POST | `/api/events/notes` | Ya existe en `/api/relations/note-event` |
| DELETE | `/api/events/{id}/notes/{note_id}` | Ya existe en `/api/relations/note-event` |

### Endpoints que se agregan

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/events/{id}/related` | Retorna tags, tasks y notes vinculados |
| POST | `/api/events/{id}/tags` | Asigna una etiqueta al evento |
| DELETE | `/api/events/{id}/tags/{tag_id}` | Desvincula una etiqueta del evento |

### Endpoints que se modifican (response limpio)

| Método | Endpoint | Qué cambia |
|---|---|---|
| POST | `/api/events/` | Response ya no incluye `tasks` ni `notes` |
| GET | `/api/events/` | Response ya no incluye `tasks` ni `notes` |
| GET | `/api/events/{id}` | Response ya no incluye `tasks` ni `notes` |
| PATCH | `/api/events/{id}` | Response ya no incluye `tasks` ni `notes` |

---

## Orden de ejecución recomendado

```
schemas.py (Pasos 1–3)
    → api.py queries (Pasos 4–6)
        → api.py eliminar endpoints (Pasos 7–10)
            → api.py nuevos endpoints (Pasos 11–13)
                → tags/schemas.py (Paso 14)
                    → tags/api.py (Paso 15)
```

Hacer deploy y validar el OpenAPI después de cada bloque antes de continuar con el siguiente.

---

## Validación final

Una vez completados todos los pasos, verificar en el OpenAPI (`/openapi.json`) que:

- `EventResponse` no contiene `tasks` ni `notes` en su schema
- Existen los paths `GET /api/events/{event_id}/related`, `POST /api/events/{event_id}/tags` y `DELETE /api/events/{event_id}/tags/{tag_id}`
- No existen los paths `POST /api/events/tasks`, `DELETE /api/events/{event_id}/tasks/{task_id}`, `POST /api/events/notes`, `DELETE /api/events/{event_id}/notes/{note_id}`
- `TagUpdate` en el schema de components incluye el campo `icon`

---