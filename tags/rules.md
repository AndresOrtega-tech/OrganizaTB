---
alwaysApply: false
scope: tags
---

# Reglas de Tags (Etiquetas)

Este documento define el funcionamiento del módulo de etiquetas. Mantenerlo actualizado con cualquier cambio en `tags/api.py` y `tags/schemas.py`.

## 1. Filosofía del módulo

Las etiquetas son **propiedad del usuario**, no de ninguna entidad en particular. El usuario crea su propio catálogo de etiquetas y las asigna a tareas, notas y eventos. La gestión CRUD de etiquetas vive aquí; la asignación/desasignación a entidades vive en el módulo de cada entidad respectiva.

**Restricción clave:** Un usuario no puede tener dos etiquetas con el mismo nombre. Sí pueden existir etiquetas con el mismo nombre entre distintos usuarios.

---

## 2. Endpoints (Tags)

### Listar etiquetas
**GET** `/api/tags/`

**Response (200 OK):**
```json
[
  {
    "id": "uuid-tag",
    "name": "Trabajo",
    "color": "#FF5733",
    "icon": null,
    "user_id": "uuid-user",
    "created_at": "2026-02-19T10:00:00Z"
  }
]
```

> Retorna todas las etiquetas del usuario autenticado. No hay filtros ni paginación — el catálogo completo se carga de una sola vez. El frontend lo usa para mostrar el selector de etiquetas en tareas, notas y eventos.

---

### Crear etiqueta
**POST** `/api/tags/`

**Request:**
```json
{
  "name": "Trabajo",
  "color": "#FF5733"
}
```

**Response (201 Created):**
```json
{
  "id": "uuid-tag",
  "name": "Trabajo",
  "color": "#FF5733",
  "icon": null,
  "user_id": "uuid-user",
  "created_at": "2026-02-19T10:00:00Z"
}
```

**Errores:**
- `409` si ya existe una etiqueta con ese nombre para el mismo usuario.

---

### Actualizar etiqueta
**PATCH** `/api/tags/{tag_id}`

**Request (todos los campos opcionales):**
```json
{
  "name": "Nuevo nombre",
  "color": "#3498DB"
}
```

**Response (200 OK):** misma estructura que POST.

**Errores:**
- `404` si la etiqueta no existe o no pertenece al usuario.
- `409` si el nuevo nombre ya lo tiene otra etiqueta del mismo usuario.

> El campo `icon` no está incluido en `TagUpdate` actualmente. Para modificar el ícono se requiere extender el schema.

---

### Eliminar etiqueta
**DELETE** `/api/tags/{tag_id}`

**Response (204 No Content)**

> Al eliminar una etiqueta, las asociaciones en `task_tags`, `note_tags` y `event_tags` se eliminan automáticamente por la restricción `ON DELETE CASCADE` de la base de datos.

---

## 3. Dónde vive la asignación de etiquetas

La vinculación de una etiqueta a una entidad **no** se hace desde este módulo. Cada entidad tiene sus propios endpoints para ello:

| Acción | Endpoint |
|---|---|
| Asignar tag a tarea | `POST /api/tasks/{id}/tags` con body `{ "tag_id": "uuid" }` |
| Quitar tag de tarea | `DELETE /api/tasks/{id}/tags/{tag_id}` |
| Asignar tag a nota | `POST /api/notes/{id}/tags` con body `{ "tag_id": "uuid" }` |
| Quitar tag de nota | `DELETE /api/notes/{id}/tags/{tag_id}` |
| Asignar tag a evento | `POST /api/events/{id}/tags` con body `{ "tag_id": "uuid" }` (pendiente) |
| Quitar tag de evento | `DELETE /api/events/{id}/tags/{tag_id}` (pendiente) |

---

## 4. Tabla de base de datos utilizada

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | Generado automáticamente |
| `user_id` | UUID | Referencia al usuario propietario |
| `name` | TEXT | Requerido, único por usuario |
| `color` | TEXT | Hex color, default `#808080` |
| `icon` | TEXT | Opcional, nombre del ícono |
| `created_at` | TIMESTAMPTZ | Automático |

Las tablas de unión son `task_tags`, `note_tags` y `event_tags`, todas con `ON DELETE CASCADE`.

## 5. Notas de implementación
- El color default es `#808080` (gris) si no se envía en la creación.
- El `icon` se almacena en BD pero aún no está expuesto en `TagUpdate` — pendiente de agregar.
- La unicidad de nombre por usuario está garantizada por constraint `UNIQUE(user_id, name)` en la BD.