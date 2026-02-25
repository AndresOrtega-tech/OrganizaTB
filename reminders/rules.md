---
alwaysApply: false
scope: reminders
---

# Reglas de Reminders (Recordatorios)

Este documento define el funcionamiento del módulo de recordatorios. Mantenerlo actualizado con cualquier cambio en `reminders/api.py` y `reminders/schemas.py`.

## 1. Filosofía del módulo

Los recordatorios **no se crean directamente** desde este módulo. Se generan automáticamente como parte del ciclo de vida de una tarea o un evento cuando se especifica la configuración de recordatorio al crear o actualizar la entidad.

Este módulo existe para dos casos de uso específicos: **consultar** todos los recordatorios del usuario (útil para el sistema de notificaciones) y **actualizar/eliminar** recordatorios individuales si es necesario.

---

## 2. Cómo se generan los recordatorios

Al crear o actualizar una tarea o evento con el campo `reminders`, el backend calcula automáticamente el `remind_at`:

```
remind_at = due_date (tarea) o start_time (evento) - offset del recordatorio
```

**Ejemplo de configuración:**
```json
"reminders": [
  { "unit": "minutes", "value": 30 },
  { "unit": "hours", "value": 2 }
]
```

**Unidades válidas:** `minutes`, `hours`, `days`

Si se actualiza `reminders` en una tarea o evento existente, los recordatorios anteriores se **reemplazan completamente**. Si se envía lista vacía `[]`, se eliminan todos los recordatorios.

---

## 3. Endpoints (Reminders)

### Listar recordatorios
**GET** `/api/reminders/`

**Query params:**
- `status`: `pending` | `sent` | `failed` (opcional)
- `start_date`: ISO 8601 — desde esta fecha de recordatorio (opcional)
- `end_date`: ISO 8601 — hasta esta fecha de recordatorio (opcional)

**Response (200 OK):**
```json
[
  {
    "id": "uuid-reminder",
    "user_id": "uuid-user",
    "task_id": "uuid-task",
    "event_id": null,
    "remind_at": "2026-02-20T09:30:00Z",
    "status": "pending",
    "created_at": "2026-02-19T10:00:00Z",
    "task_title": "Nombre de la tarea",
    "event_title": null
  }
]
```

> Incluye `task_title` o `event_title` según corresponda, para que el frontend pueda mostrar el contexto sin hacer requests adicionales. Un recordatorio pertenece a una tarea **o** a un evento, nunca a ambos.

---

### Actualizar recordatorio
**PATCH** `/api/reminders/{reminder_id}`

**Request (todos los campos opcionales):**
```json
{
  "remind_at": "2026-02-20T08:00:00Z",
  "status": "pending"
}
```

**Response (200 OK):** misma estructura que el item del listado.

**Errores:**
- `404` si el recordatorio no existe o no pertenece al usuario.

---

### Eliminar recordatorio
**DELETE** `/api/reminders/{reminder_id}`

**Response (204 No Content)**

---

## 4. Ciclo de vida de un recordatorio

| Estado | Descripción |
|---|---|
| `pending` | Recordatorio programado, aún no enviado |
| `sent` | Notificación enviada exitosamente |
| `failed` | El envío falló (error en el sistema de notificaciones) |

El cambio de estado de `pending` a `sent` o `failed` lo realiza el sistema de notificaciones (worker externo o función de Supabase), no el usuario directamente.

---

## 5. Tabla de base de datos utilizada

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | Generado automáticamente |
| `user_id` | UUID | Referencia al usuario propietario |
| `task_id` | UUID | Nullable — referencia a la tarea (si aplica) |
| `event_id` | UUID | Nullable — referencia al evento (si aplica) |
| `remind_at` | TIMESTAMPTZ | Fecha/hora exacta del recordatorio |
| `status` | TEXT | `pending`, `sent` o `failed` |
| `created_at` | TIMESTAMPTZ | Automático |

## 6. Notas de implementación
- Un recordatorio tiene `task_id` **o** `event_id`, nunca ambos. La BD debe tener un check constraint que garantice esto (pendiente de agregar).
- Los recordatorios heredan el `user_id` de la tarea o evento al que pertenecen.
- Al eliminar una tarea o evento, sus recordatorios se eliminan automáticamente por `ON DELETE CASCADE`.
- El campo `has_reminder` en tasks y events es un boolean de conveniencia que se actualiza automáticamente cuando se crean o eliminan recordatorios asociados.