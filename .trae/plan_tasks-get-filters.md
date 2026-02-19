# Plan: Refactor GET /api/tasks/ según nueva especificación de filtros

Objetivo
- Alinear GET /api/tasks/ con el documento `.trae/Tasks_get _filtros.md`.
- Soportar modos `view=home` y `view=tasks` con comportamiento claro y predecible.

Alcance
- Modificar `tasks/api.py` (list_tasks):
  - Reemplazar firma actual de parámetros por: `view`, `tab`, `tag_ids`, `priority`, `end_date`, `limit`, `cursor`.
  - Implementar lógica diferenciada para:
    - `view=home`: reglas fijas; ignora filtros manipulables.
    - `view=tasks`: tabs `pending` / `completed`, aplica filtros user-controlled.
  - Mantener modo sin `view` como deprecado pero funcional (comportamiento simple por compatibilidad).
- Actualizar contratos en:
  - `tasks/rules.md` (sección GET /api/tasks/).
  - `.trae/rules/tasks.md` (resumen corto de reglas).

Diseño de comportamiento
- `view=home`:
  - Backend aplica reglas fijas sobre `due_date` y `is_completed` (ventana hoy → hoy+7d, atrasadas pendientes, completadas solo en ventana).
  - Ignora: `tab`, `tag_ids`, `priority`, `end_date` aunque vengan.
  - Usa `limit` y `cursor` para paginación por `due_date`.
- `view=tasks`:
  - `tab=pending` (default): solo pendientes; atrasadas primero, luego futuras; sin fecha al final.
  - `tab=completed`: solo completadas; `due_date` DESC; sin fecha al final.
  - Filtros activos: `tag_ids` (AND), `priority`, `end_date`.
  - `limit` y `cursor` para paginación.
- Sin `view`:
  - Mantener comportamiento actual mínimo (por definir en regla deprecada) sin invertir mucho en lógica nueva.

Notas técnicas
- Seguir usando Supabase con joins mínimos necesarios para filtros por tags (`task_tags!inner` cuando `tag_ids` exista).
- Mapping de recordatorios igual que hoy (`reminders` → `reminders_data`).
- No incluir relaciones en la respuesta (tags/notes/events); para eso existe GET `/api/tasks/{id}/related`.

Checklist
- [ ] Actualizar firma y lógica de `list_tasks` en `tasks/api.py`.
- [ ] Implementar reglas `view=home` y `view=tasks` tal como en `.trae/Tasks_get _filtros.md`.
- [ ] Mantener modo sin `view` como deprecado/documentado.
- [ ] Actualizar documentación en `tasks/rules.md`.
- [ ] Actualizar resumen en `.trae/rules/tasks.md`.
