# `GET /api/tasks/` — Filtros y Comportamiento Completo · organizaT
**Fecha:** Febrero 2026
**Rama:** dev

---

## Modos de uso

El endpoint tiene dos modos según si se manda `view` o no.

---

## Modo `view=home` — Vista Inicio

El usuario **no manipula filtros**. El backend aplica las reglas fijas:

**Reglas:**
1. Tareas pendientes atrasadas (`is_completed=false` y `due_date < hoy`)
2. Tareas pendientes y completadas de hoy y futuro (`due_date >= hoy` y `due_date <= hoy + 7 días`)
3. Las completadas van al final — ordenadas por `due_date ASC`, completadas después de pendientes

**Ordenamiento:**
```
1. Pendientes atrasadas → due_date ASC
2. Pendientes futuras   → due_date ASC
3. Completadas          → due_date ASC, al final
```

**Params que acepta:**
- `limit` — default 10, máximo 50
- `cursor` — para paginación

**Params que ignora aunque vengan:**
- `tab`, `tag_ids`, `priority`, `end_date`, `is_completed`

**No tiene paginación por cursor en el sentido estricto** — carga todo el rango de 7 días. Si el usuario tiene muchas tareas en ese rango, el `limit` aplica igual.

---

## Modo `view=tasks` — Vista Tareas

El usuario **sí puede aplicar filtros**. Tiene dos tabs.

### Tab `pending` (default)

**Reglas fijas:**
- Solo tareas pendientes (`is_completed=false`)
- Atrasadas primero, luego futuras sin límite de fecha
- Sin `due_date` al final

**Ordenamiento:**
```
1. Atrasadas   → due_date ASC
2. Futuras     → due_date ASC
3. Sin fecha   → al final
```

### Tab `completed`

**Reglas fijas:**
- Solo tareas completadas (`is_completed=true`)
- Ordenadas por `due_date DESC` (las más recientes primero)
- Sin `due_date` al final

---

## Filtros manipulables por el usuario (aplican en ambos tabs)

| Param | Tipo | Descripción | Comportamiento si no se manda |
|-------|------|-------------|-------------------------------|
| `tag_ids` | `array<string>` | AND — la tarea debe tener TODAS las etiquetas | Sin filtro de etiqueta |
| `priority` | `string` | `baja`, `media` o `alta` | Sin filtro de prioridad |
| `end_date` | `datetime` | Tareas con `due_date` hasta esta fecha | Sin límite de fecha |
| `tab` | `string` | `pending` o `completed` | Default: `pending` |

---

## Paginación (aplica en ambos tabs)

| Param | Descripción |
|-------|-------------|
| `limit` | Default: 10, máximo: 50 |
| `cursor` | `due_date` ISO 8601 del último resultado recibido |

**Response shape:**
```json
{
  "data": [...],
  "next_cursor": "2026-03-01T00:00:00Z",
  "has_more": true
}
```

---

## Modo sin `view` — Deprecado

El modo clásico sin `view` queda deprecado. No se elimina para no romper nada, pero no se usa en ninguna vista activa. En el futuro se puede remover.

---

## Params eliminados del schema

Estos params existían antes y se remueven porque generaban confusión:

| Param | Razón |
|-------|-------|
| `start_date` | No se usaba en ninguna vista |
| `date_field` | Siempre es `due_date`, no tiene sentido exponerlo |
| `sort_by` | Siempre `due_date`, fijo |
| `order` | Fijo según el modo — no manipulable por el usuario |
| `is_completed` | Lo maneja `tab` automáticamente en modo `view=tasks` |

---

## Resumen de params por modo

| Param | `view=home` | `view=tasks` |
|-------|-------------|--------------|
| `tab` | ✗ ignorado | ✓ `pending` / `completed` |
| `tag_ids` | ✗ ignorado | ✓ |
| `priority` | ✗ ignorado | ✓ |
| `end_date` | ✗ ignorado | ✓ |
| `limit` | ✓ | ✓ |
| `cursor` | ✓ | ✓ |

---