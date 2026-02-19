# Plan: Ajustes PATCH (null fields) y body de tags en Tasks

Objetivo
- Permitir limpiar campos en PATCH (`null` válido), especialmente `due_date`.
- Simplificar el body de asignación de etiquetas para `POST /api/tasks/{task_id}/tags` a `{ "tag_id": "..." }`.

Alcance y contratos
1) PATCH `/api/tasks/{task_id}`
- Usar `exclude_unset=True` para distinguir "no enviado" vs "enviado como null".
- `due_date`:
  - Si se envía `null`, se actualiza a `NULL` en la BD.
  - Solo convertir a ISO cuando `due_date` no sea `None`.
- `reminders`:
  - Si `reminders` se envía (lista vacía o con elementos): borrar existentes y, si hay `due_date` no nulo y lista no vacía, recalcular e insertar; en caso contrario, `has_reminder = False`.
  - Si `reminders` no se envía: mantener la política actual (no tocar recordatorios, aunque cambie `due_date`).
- Mantener `updated_at = now`.

2) POST `/api/tasks/{task_id}/tags`
- Request body: `{ "tag_id": "uuid" }` (se elimina `task_id` del body).
- Lógica:
  - Validar pertenencia de la tarea al usuario.
  - Idempotencia: si ya existe (task_id, tag_id) → `assigned: 0`.
  - Insertar relación si no existe → `assigned: 1`.
- Response (200):
```json
{ "message": "Etiqueta asignada correctamente", "assigned": 0 | 1 }
```

3) GET `/api/tasks` con `view=home`
- Mover parte del filtrado a la BD:
  - Consultar solo:
    - Tareas pendientes atrasadas (`is_completed=false` y `due_date < hoy`).
    - Tareas (pendientes y completadas) con `due_date` entre `hoy` y `hoy + 7 días`.
  - Mantener en Python la lógica de orden:
    - Pendientes atrasadas (por `due_date` asc).
    - Pendientes futuras (por `due_date` asc).
    - Completadas futuras (por `due_date` asc).
- Reutilizar `_due_dt`:
  - Guardar el `datetime` parseado una sola vez por tarea.
  - Usar `_due_dt` para:
    - Filtrar por `cursor` (`_due_dt > cursor`).
    - Calcular `next_cursor` (`next_cursor = último _due_dt de la página`).
  - Evitar nuevos `datetime.fromisoformat()` sobre `due_date` en la rama `view=home`.

Archivos a modificar
- `tasks/schemas.py`: actualizar `TaskAssignTags` para que solo tenga `tag_id`.
- `tasks/api.py`:
  - `update_task`: usar `exclude_unset=True`; soportar `due_date=None`; respetar la lógica de `reminders`.
  - `assign_tag_to_task`: consumir solo `tag_id` del body, `task_id` del path; mantener idempotencia.
  - `list_tasks`: optimizar rama `view=home` con filtro parcial en BD y reutilización de `_due_dt` para cursor.
- `tasks/rules.md` y `.trae/rules/tasks.md`: documentar el body nuevo de tags y la semántica de PATCH.

No cambia
- Esquema de BD, migraciones y permisos.
- Rutas existentes distintas a las descritas.

Compatibilidad
- No se agrega endpoint legacy `/api/tasks/tags` por ahora (contrato nuevo preferido).
- Clientes que aún envíen `task_id` en el body deberán actualizarse.

Validación
- Compilación de Python (`python -m compileall .`).
- Pruebas manuales:
  - PATCH con `{"due_date": null}` y verificar `due_date` en DB y `has_reminder`.
  - POST `/api/tasks/{id}/tags` con `{"tag_id": ...}` dos veces y verificar `assigned: 1` luego `0`.

Riesgos
- Clientes antiguos enviando `task_id` en body → 422; mitigación: comunicación y actualización del frontend.
- `due_date` a `NULL` con recordatorios existentes y sin `reminders` en el PATCH: se mantienen (semántica actual).

Checklist
- [ ] Actualizar `TaskAssignTags` (solo `tag_id`)
- [ ] Ajustar `assign_tag_to_task` (usar path `task_id`, idempotencia)
- [ ] Cambiar `update_task` a `exclude_unset=True` y soportar `None`
- [ ] Actualizar documentación en rules
- [ ] Validación manual y compilación
