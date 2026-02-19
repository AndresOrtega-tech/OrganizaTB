---
alwaysApply: false
scope: relations
---

# Reglas de Relations

Este documento define el funcionamiento del módulo de vinculaciones entre entidades (tareas, notas y eventos). Mantenerlo actualizado con cualquier cambio en `relations/api.py` y `relations/schemas.py`.

## 1. Filosofía del módulo

Las vinculaciones entre tareas, notas y eventos son relaciones **simétricas y neutrales**: ninguna entidad es dueña de la otra. Por eso se agrupan en un módulo independiente en lugar de vivir dentro de tasks, notes o events.

Las vinculaciones de **etiquetas (tags)** siguen siendo propiedad de cada entidad (tarea, nota, evento), ya que el tag se asigna "a" algo concreto. Esas permanecen en sus respectivos módulos.

## 2. Endpoints (Relations)

### Vincular tarea ↔ nota
**POST** `/api/relations/task-note`

**Request:**
```json
{
  "task_id": "uuid-task",
  "note_id": "uuid-note"
}
```

**Response (201 Created):**
```json
{
  "message": "Tarea y nota vinculadas exitosamente"
}
```

**Errores:**
- `404` si la tarea o la nota no existen o no pertenecen al usuario.
- `409` si la vinculación ya existe.

---

### Desvincular tarea ↔ nota
**DELETE** `/api/relations/task-note`

**Request body:**
```json
{
  "task_id": "uuid-task",
  "note_id": "uuid-note"
}
```

**Response (200 OK):**
```json
{
  "message": "Vinculación entre tarea y nota eliminada exitosamente"
}
```

**Errores:**
- `404` si la vinculación no existe.

---

### Vincular tarea ↔ evento
**POST** `/api/relations/task-event`

**Request:**
```json
{
  "task_id": "uuid-task",
  "event_id": "uuid-event"
}
```

**Response (201 Created):**
```json
{
  "message": "Tarea y evento vinculados exitosamente"
}
```

**Errores:**
- `404` si la tarea o el evento no existen o no pertenecen al usuario.
- `409` si la vinculación ya existe.

---

### Desvincular tarea ↔ evento
**DELETE** `/api/relations/task-event`

**Request body:**
```json
{
  "task_id": "uuid-task",
  "event_id": "uuid-event"
}
```

**Response (200 OK):**
```json
{
  "message": "Vinculación entre tarea y evento eliminada exitosamente"
}
```

**Errores:**
- `404` si la vinculación no existe.

---

### Vincular nota ↔ evento
**POST** `/api/relations/note-event`

**Request:**
```json
{
  "note_id": "uuid-note",
  "event_id": "uuid-event"
}
```

**Response (201 Created):**
```json
{
  "message": "Nota y evento vinculados exitosamente"
}
```

**Errores:**
- `404` si la nota o el evento no existen o no pertenecen al usuario.
- `409` si la vinculación ya existe.

---

### Desvincular nota ↔ evento
**DELETE** `/api/relations/note-event`

**Request body:**
```json
{
  "note_id": "uuid-note",
  "event_id": "uuid-event"
}
```

**Response (200 OK):**
```json
{
  "message": "Vinculación entre nota y evento eliminada exitosamente"
}
```

**Errores:**
- `404` si la vinculación no existe.

---

## 3. Tablas de base de datos utilizadas

| Relación       | Tabla en BD     | Columnas clave              |
|----------------|-----------------|-----------------------------|
| Tarea ↔ Nota   | `task_notes`    | `task_id`, `note_id`        |
| Tarea ↔ Evento | `event_tasks`   | `event_id`, `task_id`       |
| Nota ↔ Evento  | `event_notes`   | `event_id`, `note_id`       |

> Nota: La tabla `event_tasks` tiene `event_id` como primera columna, pero la relación se trata simétricamente desde la API.

## 4. Validaciones requeridas

Antes de crear o eliminar cualquier vinculación, el backend debe:
1. Verificar que el usuario autenticado es propietario de **ambas** entidades involucradas.
2. Para POST: verificar que la vinculación no exista ya (evitar duplicados, retornar 409).
3. Para DELETE: verificar que la vinculación exista (retornar 404 si no).

## 5. Migración desde Tasks

Los siguientes endpoints de tasks quedan **deprecados** y son reemplazados por este módulo:

| Endpoint deprecado                          | Reemplazado por                        |
|---------------------------------------------|----------------------------------------|
| `POST /api/tasks/notes`                     | `POST /api/relations/task-note`        |
| `DELETE /api/tasks/{id}/notes/{note_id}`    | `DELETE /api/relations/task-note`      |

Durante la migración se debe actualizar el documento `Reglas_Backend_Tasks` para remover esos endpoints del listado.

## 6. Lectura de relaciones

Las relaciones **no se consultan** desde este módulo. Para leer qué elementos están vinculados a una entidad, se usan los endpoints `/related` de cada módulo:

- `GET /api/tasks/{id}/related` → retorna notes y events vinculados a la tarea.
- `GET /api/notes/{id}/related` → retorna tasks y events vinculados a la nota.
- `GET /api/events/{id}/related` → retorna tasks y notes vinculados al evento (cuando se implemente).