# Plan: Cambiar POST /api/tasks/tags a un solo tag

Objetivo
- Pasar de payload batch { task_id, tag_ids[] } a payload único { task_id, tag_id }.

Alcance
- Modificar tasks/schemas.py: TaskAssignTags -> reemplazar tag_ids: List[str] por tag_id: str (mismo nombre de modelo).
- Modificar tasks/api.py: endpoint POST /api/tasks/tags para insertar una sola relación (upsert/ignore duplicados).
- Respuesta propuesta: { "message": "Etiqueta asignada correctamente", "assigned": 1|0 } donde 0 implica relación ya existente (idempotente).
- Documentación: Actualizar tasks/rules.md y .trae/rules/tasks.md.

Detalles de implementación
- Validar que la tarea pertenece al usuario (igual que hoy).
- Insertar en task_tags un solo registro { task_id, tag_id } con upsert on_conflict="task_id, tag_id", ignore_duplicates=True.
- Manejar retorno assigned=1 si insertó; assigned=0 si ya existía (según response de Supabase).

No Cambia
- Endpoint y ruta se mantienen: POST /api/tasks/tags.
- Seguridad y dependencias (get_current_user) sin cambios.

Riesgos
- Clientes que aún envíen tag_ids fallarán (breaking change). Documentar claramente.

Checklist
- [ ] Actualizar schema TaskAssignTags
- [ ] Ajustar lógica en tasks/api.py
- [ ] Actualizar reglas en tasks/rules.md y .trae/rules/tasks.md
- [ ] Verificación manual con request real
