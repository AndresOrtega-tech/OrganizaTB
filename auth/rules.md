# OrganizaT — Resumen del Backend

Este documento es la referencia rápida del estado actual de todos los módulos del backend. Para el detalle completo de cada módulo, consultar su archivo de reglas correspondiente.

---

## Estado general por módulo

| Módulo | Estado | Pendiente |
|---|---|---|
| 🔒 Auth | ✅ Completo | — |
| ✅ Tasks | ✅ Completo | — |
| ✍️ Notes | ✅ Completo | — |
| 🔗 Relations | ✅ Completo | — |
| 🏷 Tags | ✅ Completo | Agregar `icon` a `TagUpdate` |
| 📝 Reminders | ✅ Completo | Check constraint `task_id XOR event_id` en BD |
| 🗓 Events | 🔄 En refactorización | Ver sección de pendientes |
| 💡 Insights | ⏳ Por hacer | Se implementa al final |

---

## 🔒 Auth — Autenticación y Usuarios

**Estado: Completo ✅**

Gestiona el registro, login y perfil del usuario. La autenticación se delega a Supabase Auth; el backend actúa como intermediario y retorna tokens JWT.

**Endpoints disponibles:**
- `POST /api/users` — Registro de usuario nuevo
- `POST /api/auth/login` — Login, retorna `access_token` y `refresh_token`
- `GET /api/users/me` — Perfil del usuario autenticado
- `PATCH /api/users/avatar` — Actualizar avatar (único por usuario)
- `PATCH /api/users/password` — Cambiar contraseña (requiere estar autenticado)
- `POST /api/users/password/reset` — Solicitar recuperación de contraseña por correo

**Reglas clave:**
- El `avatar` es un identificador tipo username, no una URL. Debe ser único entre todos los usuarios.
- Al registrarse, un trigger de Supabase crea automáticamente el registro en `public.profiles`.
- Todos los endpoints del sistema (excepto registro, login y reset) requieren `Authorization: Bearer {token}`.
- RLS está habilitado en todas las tablas — Supabase filtra automáticamente por `auth.uid()`.

---

## ✅ Tasks — Tareas

**Estado: Completo ✅**

Gestiona el ciclo de vida completo de las tareas con paginación cursor y dos modos de vista.

**Endpoints disponibles:**
- `POST /api/tasks/` — Crear tarea
- `GET /api/tasks/` — Listar tareas (paginado con cursor)
- `GET /api/tasks/{id}` — Obtener tarea por ID
- `PATCH /api/tasks/{id}` — Actualizar tarea
- `DELETE /api/tasks/{id}` — Eliminar tarea
- `GET /api/tasks/{id}/related` — Tags, notas y eventos vinculados
- `POST /api/tasks/{id}/tags` — Asignar etiqueta
- `DELETE /api/tasks/{id}/tags/{tag_id}` — Quitar etiqueta

**Reglas clave:**
- `view=home`: ventana hoy → hoy+7 días. Muestra pendientes atrasadas, pendientes en ventana y completadas en ventana. No muestra completadas atrasadas ni tareas sin `due_date`.
- `view=tasks`: tab `pending` (atrasadas primero, luego futuras, sin fecha al final) y tab `completed` (por `due_date` desc, sin fecha al final).
- Paginación por cursor basado en `due_date`.
- Las relaciones con notas y eventos se crean/eliminan desde **Relations**.
- Recordatorios: `remind_at = due_date - offset`.

---

## ✍️ Notes — Notas

**Estado: Completo ✅**

Gestiona notas con soporte de archivado, filtrado por tags y campo `summary` para IA futura.

**Endpoints disponibles:**
- `POST /api/notes/` — Crear nota
- `GET /api/notes/` — Listar notas
- `GET /api/notes/{id}` — Obtener nota por ID
- `PATCH /api/notes/{id}` — Actualizar nota
- `PATCH /api/notes/{id}/summary` — Actualizar solo el resumen (acepta `null`)
- `DELETE /api/notes/{id}` — Eliminar nota
- `GET /api/notes/{id}/related` — Tags, tareas y eventos vinculados
- `POST /api/notes/{id}/tags` — Asignar etiqueta
- `DELETE /api/notes/{id}/tags/{tag_id}` — Quitar etiqueta

**Reglas clave:**
- `NoteResponse` retorna solo campos base — sin `tags`, `tasks` ni `events` embebidos.
- Listado filtra por `is_archived` (default `false`), orden por `updated_at` desc por defecto.
- Para el home, el frontend manda `limit=3&sort_by=updated_at&order=desc`.
- Las relaciones con tareas y eventos se gestionan desde **Relations**.

---

## 🔗 Relations — Vinculaciones

**Estado: Completo ✅**

Módulo independiente que gestiona las vinculaciones simétricas entre entidades. Ninguna entidad es dueña de la relación.

**Endpoints disponibles:**
- `POST /api/relations/task-note` — Vincular tarea ↔ nota
- `DELETE /api/relations/task-note` — Desvincular tarea ↔ nota
- `POST /api/relations/task-event` — Vincular tarea ↔ evento
- `DELETE /api/relations/task-event` — Desvincular tarea ↔ evento
- `POST /api/relations/note-event` — Vincular nota ↔ evento
- `DELETE /api/relations/note-event` — Desvincular nota ↔ evento

**Reglas clave:**
- El backend verifica que el usuario sea propietario de **ambas** entidades antes de vincular o desvincular.
- `POST` retorna `409` si la vinculación ya existe. `DELETE` retorna `404` si no existe.
- Las relaciones **no se leen** desde aquí — se leen desde el endpoint `/related` de cada entidad.
- Los tags no pasan por este módulo — pertenecen a cada entidad.

**Tablas utilizadas:**

| Relación | Tabla |
|---|---|
| Tarea ↔ Nota | `task_notes` |
| Tarea ↔ Evento | `event_tasks` |
| Nota ↔ Evento | `event_notes` |

---

## 🏷 Tags — Etiquetas

**Estado: Completo ✅ (con un pendiente menor)**

Gestiona el catálogo de etiquetas del usuario. La asignación a entidades vive en el módulo de cada entidad.

**Endpoints disponibles:**
- `GET /api/tags/` — Listar todas las etiquetas del usuario
- `POST /api/tags/` — Crear etiqueta
- `PATCH /api/tags/{tag_id}` — Actualizar nombre y/o color
- `DELETE /api/tags/{tag_id}` — Eliminar etiqueta (cascade automático en `task_tags`, `note_tags`, `event_tags`)

**Reglas clave:**
- Nombre único por usuario (constraint `UNIQUE(user_id, name)` en BD).
- Color default `#808080` si no se envía.
- El catálogo completo se carga sin paginación — se usa para el selector de tags en todo el sistema.

**Pendiente:**
- El campo `icon` existe en BD y en `TagResponse` pero no está en `TagUpdate`. Pendiente agregar al schema para permitir editarlo.

---

## 📝 Reminders — Recordatorios

**Estado: Completo ✅ (con un pendiente en BD)**

Los recordatorios se generan automáticamente desde Tasks y Events. Este módulo permite consultarlos y gestionarlos individualmente.

**Endpoints disponibles:**
- `GET /api/reminders/` — Listar recordatorios (filtros: `status`, `start_date`, `end_date`)
- `PATCH /api/reminders/{id}` — Actualizar `remind_at` o `status`
- `DELETE /api/reminders/{id}` — Eliminar recordatorio individual

**Reglas clave:**
- Los recordatorios **no se crean** desde este módulo — se generan al crear/actualizar una tarea o evento.
- Fórmula: `remind_at = due_date (tarea) o start_time (evento) - offset`.
- Si se actualiza `reminders` en una tarea/evento, los anteriores se reemplazan completamente. Lista vacía `[]` los elimina todos.
- Cada recordatorio pertenece a una tarea **o** a un evento, nunca a ambos.
- El response incluye `task_title` o `event_title` para evitar requests adicionales del frontend.
- Estados posibles: `pending`, `sent`, `failed`. El cambio de estado lo hace el worker de notificaciones, no el usuario.

**Pendiente en BD:**
- Agregar check constraint `(task_id IS NOT NULL) XOR (event_id IS NOT NULL)` para garantizar que un reminder no pueda tener ambos o ninguno.

---

## 🗓 Events — Eventos

**Estado: En refactorización 🔄**

El CRUD está completo y funcional, pero el módulo aún no sigue el patrón limpio de Tasks y Notes. Está pendiente la misma refactorización que se le hizo a Notes.

**Endpoints disponibles (funcionando):**
- `POST /api/events/` — Crear evento
- `GET /api/events/` — Listar eventos (filtros: `start_date`, `end_date`)
- `GET /api/events/{id}` — Obtener evento por ID
- `PATCH /api/events/{id}` — Actualizar evento
- `DELETE /api/events/{id}` — Eliminar evento

**Endpoints deprecados (funcionando, pero pendientes de migrar):**

| Endpoint actual | Reemplazado por |
|---|---|
| `POST /api/events/tasks` | `POST /api/relations/task-event` |
| `DELETE /api/events/{id}/tasks/{task_id}` | `DELETE /api/relations/task-event` |
| `POST /api/events/notes` | `POST /api/relations/note-event` |
| `DELETE /api/events/{id}/notes/{note_id}` | `DELETE /api/relations/note-event` |

**Pendientes de implementar:**

| Prioridad | Qué | Descripción |
|---|---|---|
| Alta | Limpiar `EventResponse` | Quitar `tasks` y `notes` embebidos — mismo paso que se hizo con Notes |
| Alta | `GET /api/events/{id}/related` | Tags, tareas y notas vinculadas — mismo patrón que Tasks y Notes |
| Alta | `POST /api/events/{id}/tags` | Asignar etiqueta al evento |
| Alta | `DELETE /api/events/{id}/tags/{tag_id}` | Quitar etiqueta del evento |
| Alta | Migrar vinculaciones | Eliminar endpoints deprecados una vez que Relations los cubra |

**Reglas del listado:**
- Sin filtros: todos los eventos del usuario ordenados por `start_time` asc.
- Con rango: filtra por `start_time` dentro del rango.
- No hay paginación cursor (a diferencia de Tasks).
- Para el home, el frontend manda `start_date=hoy&end_date=hoy+7días`.

---

## 💡 Insights — Análisis de Mejora

**Estado: Por hacer ⏳**

La tabla `improvement_insights` ya existe en la BD con campos `type`, `title`, `message`, `metrics` (JSONB), `is_read` y `created_at`. Se implementa cuando el resto del sistema esté estable.

---

## Resumen de pendientes

| Prioridad | Módulo | Qué hacer |
|---|---|---|
| 🔴 Alta | Events | Limpiar `EventResponse` (quitar `tasks` y `notes` embebidos) |
| 🔴 Alta | Events | Implementar `GET /api/events/{id}/related` |
| 🔴 Alta | Events | Implementar `POST/DELETE /api/events/{id}/tags` |
| 🔴 Alta | Events | Migrar endpoints de vinculación a Relations y eliminarlos de Events |
| 🟡 Media | Tags | Agregar `icon` a `TagUpdate` |
| 🟡 Media | Reminders | Agregar check constraint `task_id XOR event_id` en BD |
| 🟢 Baja | Insights | Todo — se define e implementa al final |