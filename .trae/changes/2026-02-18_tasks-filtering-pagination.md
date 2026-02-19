# 2026-02-18 · Filtrado inteligente, paginación y endpoint de relaciones en Tasks

## Contexto
Plan de trabajo definido en `Plan de accion/tareas.md`. Se implementaron los 4 bloques en orden.

---

## Cambios realizados

### Bloque 4 — Índice compuesto en Supabase
**Archivo:** `migrations/001_composite_index.sql` *(nuevo)*

SQL listo para ejecutar en el SQL Editor de Supabase antes de hacer deploy:
```sql
CREATE INDEX IF NOT EXISTS idx_tasks_user_completed_due
ON public.tasks(user_id, is_completed, due_date);
```
Cubre los filtros combinados `user_id + is_completed + due_date` que usan los Bloques 1 y 2.

---

### Bloque 1 — Param `view` en `GET /api/tasks/`
**Archivo:** `tasks/api.py`

Nuevo query param `view` con valores `home` y `tasks`. Retrocompatible: sin `view`, el comportamiento es el anterior.

| `view` | Filtro automático de `is_completed` | Filtro de fecha |
|--------|--------------------------------------|-----------------|
| `home` | `false` | `due_date ≤ hoy + 7 días` (nulls excluidos automáticamente) |
| `tasks` | `false` | Sin límite (nulls al final por `due_date ASC`) |
| *(sin view)* | respeta `is_completed` del request | respeta `start_date`/`end_date` del request |

---

### Bloque 2 — Paginación con cursor en `GET /api/tasks/`
**Archivos:** `tasks/api.py`, `tasks/schemas.py`

Nuevos params: `limit` (1–50, default 10) y `cursor` (ISO 8601 del `due_date` del último item recibido).

**Cambio de response model:** `List[TaskResponse]` → `PaginatedTaskResponse`
```json
{
  "data": [...],
  "next_cursor": "2026-03-01T00:00:00+00:00",
  "has_more": true
}
```
- Cuando `view` o `cursor` están presentes, el sort se fuerza a `due_date ASC`.
- `next_cursor` es `null` cuando no hay más páginas o el último item no tiene `due_date`.

> ⚠️ **Breaking change:** el frontend debe actualizar el consumo de `GET /api/tasks/` para leer `response.data` en vez del array directo.

---

### Bloque 3 — `GET /api/tasks/{id}/related`
**Archivos:** `tasks/api.py`, `tasks/schemas.py`

Nuevo endpoint para refrescar solo notas y eventos vinculados sin recargar el detalle completo.

**Response:**
```json
{
  "notes": [{ "id": "...", "title": "...", "content": "..." }],
  "events": [{ "id": "...", "title": "...", "start_time": "..." }]
}
```
**Cuándo usarlo:** después de un `POST /api/tasks/notes` o `POST /api/events/tasks` fallido como mecanismo de rollback del optimistic update.

---

## Schemas nuevos en `tasks/schemas.py`
- `PaginatedTaskResponse` — wrapper de paginación para `GET /api/tasks/`
- `TaskRelatedResponse` — response de `GET /api/tasks/{id}/related`

## Archivos modificados
| Archivo | Tipo de cambio |
|---------|---------------|
| `tasks/api.py` | Modificado (Bloques 1, 2 y 3) |
| `tasks/schemas.py` | Modificado (2 schemas nuevos) |
| `migrations/001_composite_index.sql` | Nuevo |
