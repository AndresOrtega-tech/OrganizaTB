# Changelog

Todos los cambios relevantes de este proyecto se documentarán en este archivo.

El formato está basado en Keep a Changelog y este proyecto utiliza versionado orientado a releases internas.

## [Sin publicar]

### Añadido
- Backend FastAPI para OrganizaT.
- Módulo de autenticación con registro, login, refresh token, perfil, cambio de avatar, cambio y recuperación de contraseña.
- CRUD completo de tareas con prioridades, fechas límite, paginación por cursor, filtros por vista y etiquetas.
- CRUD completo de notas con archivado, resumen y etiquetado.
- CRUD de eventos con recordatorios, etiquetas y relaciones cruzadas.
- Módulo de recordatorios para consulta, edición y eliminación.
- Módulo de relaciones para vincular tareas, notas y eventos.
- Endpoints de health check y utilidades para verificación de tablas.
- Despliegue serverless en Vercel.
- Reglas y planes operativos en `.windsurf/`.

### Modificado
- Reorganización de configuración del agente moviendo reglas de `.agents` a `.windsurf`.
- Refactor de eventos para alinearse con el patrón de tasks/notes y separar relaciones a `/relations`.
- Reestructuración de autenticación separando rutas de auth y users.
- Consolidación de `TagSummary` y respuestas relacionadas en tasks, notes y events.
- Optimización y refactor de listado de tareas con filtros, cursor y manejo de `due_date` nulo.
- Refactor del módulo de notas para separar datos base y relaciones.

### Corregido
- Ajuste del filtro `is_archived` por defecto en notas.
- Correcciones en manejo de tareas sin `due_date`.
- Ajustes al contrato de tags embebidos en respuestas.

### Documentación
- Documentación inicial del proyecto pendiente de confirmaciones menores sobre convenciones y contenido del directorio `supabase/`.
