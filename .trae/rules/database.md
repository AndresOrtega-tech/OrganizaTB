---
alwaysApply: false
scope: database
---

# Base de Datos
- Supabase PostgreSQL con RLS habilitado.
- IDs UUID con FKs y ON DELETE CASCADE.
- Joins con select para evitar N+1 en relaciones.
- Tablas clave: profiles, tasks, notes, events, tags, reminders.
