# MCP: Lectura de Tareas
Resumen: Diseñar y registrar un MCP que lea tareas desde Supabase/REST de OrganizaT con seguridad y compatibilidad multi-entorno.

## Alcance
- Proveer lectura de tareas (lista y detalle) vía MCP.
- No modifica datos ni activa escrituras.

## Entradas / Salidas
- Entradas: filtros (opcional: estado, etiqueta, fecha), id de tarea para detalle.
- Salidas: JSON con campos de tarea, tags, recordatorios; manejo explícito de errores (404, 401/403, timeouts).

## Consideraciones de Seguridad
- Autenticación: usar token/jwt del usuario (no service key) para respetar RLS.
- Configuración: leer creds de env; no hardcodear claves.
- RLS: confirmar políticas en `tasks`, `task_tags`, `reminders`; evitar consultas anónimas.
- Rate limits: defensivo (reintentos con backoff acotado).

## Plan de Acción
1) Inventario rápido de acceso: confirmar endpoint/base URL y método (Supabase client vs REST) y variables de entorno disponibles.
2) Diseño de funciones MCP:
   - `list_tasks(filters)`
   - `get_task(task_id)`
   - Estructura de errores uniforme.
3) Implementación del servidor MCP:
   - Cliente Supabase o fetch con headers auth.
   - Validación de inputs (max_length, formatos UUID/ISO).
4) Pruebas básicas:
   - Caso feliz: lista y detalle con usuario real.
   - Caso RLS: token sin permisos → 403/404 esperado.
   - Caso inexistente: 404 claro.
5) Documentación mínima:
   - README breve de uso, variables requeridas y ejemplos de invocación.

## Riesgos y Mitigación
- Token inválido/ausente: validar y retornar error claro.
- Entorno equivocado: parametrizar URL/keys.
- Respuestas grandes: paginación y límites razonables.
