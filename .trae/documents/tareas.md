# Plan de Trabajo — Backend · organizaT
**Fecha:** Febrero 2026

---

## Resumen

| # | Cambio | Prioridad |
|---|--------|-----------|
| 1 | Filtrado inteligente en `GET /api/tasks/` | Alta |
| 2 | Paginación con cursor en `GET /api/tasks/` | Alta |
| 3 | Nuevo endpoint `GET /api/tasks/{id}/related` | Media |
| 4 | Índice compuesto en Supabase | Alta |

---

## Bloque 1 — Filtrado inteligente en `GET /api/tasks/`

### Problema actual
El endpoint retorna todas las tareas sin discriminar por estado ni fecha. Vista Inicio y Vista Tareas necesitan comportamientos distintos pero reciben el mismo payload completo.

### Comportamiento deseado

**Vista Inicio (`view=home`):**
- Tareas pendientes **atrasadas** (due_date < hoy)
- Tareas pendientes de los **próximos 7 días** (hoy ≤ due_date ≤ hoy + 7)
- Completadas **no se cargan**

**Vista Tareas (`view=tasks`):**
- Tareas pendientes atrasadas + **todo el futuro** (sin límite de fecha)
- Completadas **no se cargan por default**

### Solución

Extender el endpoint existente con un nuevo query param `view`. Retrocompatible — si no se manda, el comportamiento es el actual.

```
GET /api/tasks/?view=home       → pendientes, máximo 7 días a futuro
GET /api/tasks/?view=tasks      → pendientes, sin límite de fecha
GET /api/tasks/                 → comportamiento actual (sin cambios)
```

**Lógica en FastAPI:**

```python
from datetime import date, timedelta

today = date.today()

if view == "home":
    query = query.eq("is_completed", False)
    query = query.lte("due_date", (today + timedelta(days=7)).isoformat())

elif view == "tasks":
    query = query.eq("is_completed", False)
    # sin filtro de fecha superior, trae atrasadas + todo el futuro
```

### Notas
- El param `is_completed` ya existe en el endpoint — solo se aplica automáticamente según `view`
- Tareas **sin `due_date`** deben aparecer al final. Definir si se incluyen en `home` o solo en `tasks`
- El campo `due_date` ya está indexado ✓

---

## Bloque 2 — Paginación con cursor en `GET /api/tasks/`

### Problema actual
Todas las tareas se cargan de un jalón. Sin paginación, el rendimiento se degrada conforme crecen los datos.

### Solución

Paginación por **cursor** usando `due_date` como campo de referencia. Más eficiente que `OFFSET` en Supabase y compatible con infinite scroll en el frontend.

**Nuevos params:**

```
GET /api/tasks/?view=tasks&limit=10&cursor=2026-03-01T00:00:00Z
```

**Lógica en FastAPI:**

```python
limit = min(params.limit or 10, 50)  # máximo 50 por seguridad

if cursor:
    query = query.gt("due_date", cursor)  # mayor que el último due_date recibido

query = query.order("due_date", desc=False).limit(limit + 1)

results = query.execute()
has_more = len(results.data) > limit
items = results.data[:limit]
next_cursor = items[-1]["due_date"] if has_more else None
```

**Response shape:**

```json
{
  "data": [...],
  "next_cursor": "2026-03-01T00:00:00Z",
  "has_more": true
}
```

### Notas
- Page size fijo de **10** como default
- `next_cursor` es `null` cuando no hay más páginas
- Este cambio se combina con el Bloque 1 — ambos params coexisten en el mismo request

---

## Bloque 3 — Nuevo endpoint `GET /api/tasks/{id}/related`

### Por qué es necesario
El detalle de tarea (`GET /api/tasks/{task_id}`) hace un JOIN que trae notas y eventos vinculados junto con el detalle completo. Esto está bien al cargar la vista por primera vez.

El problema es al **vincular o desvincular** algo nuevo: aunque hay optimistic update en el frontend, si la operación falla no hay forma de refrescar solo las relaciones sin recargar todo el detalle.

### Solución

```
GET /api/tasks/{task_id}/related
```

**Response:**

```json
{
  "notes": [
    { "id": "...", "title": "...", "content": "..." }
  ],
  "events": [
    { "id": "...", "title": "...", "start_time": "..." }
  ]
}
```

**Cuándo se llama:**
- Solo después de un `POST /api/tasks/notes` o `POST /api/tasks/{id}/events` como confirmación del optimistic update
- Si el optimistic update falla → rollback local → se llama este endpoint para sincronizar solo esa sección

**El `GET /api/tasks/{task_id}` no cambia** — sigue trayendo todo con JOIN al cargar el detalle.

---

## Bloque 4 — Índice compuesto en Supabase

Los Bloques 1 y 2 hacen queries combinando `user_id + is_completed + due_date`. Sin un índice compuesto, Supabase hace full scan por tabla.

```sql
CREATE INDEX idx_tasks_user_completed_due
ON tasks(user_id, is_completed, due_date);
```

Crear este índice **antes** de implementar los Bloques 1 y 2.

---

## Orden de implementación

```
1. Bloque 4 — índice en Supabase (5 min, prerequisito de todo lo demás)
      ↓
2. Bloque 1 — param view en GET /api/tasks/
      ↓
3. Bloque 2 — cursor pagination en GET /api/tasks/
      ↓
4. Bloque 3 — GET /api/tasks/{id}/related
```