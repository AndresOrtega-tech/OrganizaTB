# CR-002: Integración CI con GitHub Actions (tests de integración + Docker build)

> **Tipo:** MEDIUM
> **Fecha:** 2026-03-27
> **Estado:** Aprobado

---

## Descripción del cambio

Agregar dos pipelines de GitHub Actions a la rama `v_docker_prod`:

1. **CI Tests** — ejecutar tests de integración con pytest contra la API viva en Vercel, usando credenciales almacenadas como GitHub Secrets/Variables.
2. **CI Docker Build** — verificar que la imagen Docker compila correctamente en cada push/PR.

## Motivación

Requisito académico. Garantizar que cambios en `v_docker_prod` no rompan la API ni la imagen Docker antes de mergear. Proporciona una red de seguridad automatizada.

## Impacto estimado

### Documentos a actualizar
- [x] `docs/spec.md` — agregar sección US-008 CI/CD
- [x] `docs/blueprint.md` — nota de cambio CR-002
- [x] `docs/tasks.md` — agregar TASK-016 a TASK-019

### Tasks nuevas
- [ ] **TASK-016** — Crear `tests/test_integration_v1.py` con pytest
- [ ] **TASK-017** — Crear `.github/workflows/ci-tests.yml`
- [ ] **TASK-018** — Crear `.github/workflows/ci-docker.yml`
- [ ] **TASK-019** — Validar CI completo corriendo en `v_docker_prod`

### Archivos de código afectados
- `tests/test_integration_v1.py` — nuevo, tests pytest de integración contra API viva en Vercel
- `.github/workflows/ci-tests.yml` — nuevo, workflow de tests en GitHub Actions
- `.github/workflows/ci-docker.yml` — nuevo, workflow de docker build en GitHub Actions

### Variables y Secrets de GitHub requeridos
| Nombre | Tipo | Descripción |
|--------|------|-------------|
| `TEST_EMAIL` | Variable | Email del usuario de prueba |
| `TEST_PASSWORD` | **Secret** | Contraseña del usuario de prueba |
| `BASE_URL` | Variable | URL base de la API en Vercel |

### Riesgos
- Los tests golpean Supabase real → pueden generar datos sucios si no se limpian correctamente en teardown
- Si Vercel está caído, CI falla aunque el código esté correcto (flaky externo)
- `TEST_PASSWORD` debe estar en **Secrets** (no Variables) — ✅ ya corregido por el equipo

## Plan de ejecución

Re-entrada al pipeline desde: `spec.md` (nueva sección) → `tasks.md` → apply

Pasos:
1. Actualizar `docs/spec.md` y `docs/blueprint.md`
2. Agregar tasks a `docs/tasks.md`
3. ~~[GATE]~~ Aprobado por Andres — 2026-03-27
4. Ejecutar Implementer: TASK-016 → TASK-017 → TASK-018
5. Validar CI en `v_docker_prod` (TASK-019)
6. Correr `update-docs` post-implementación

## Criterio de done
- `pytest tests/test_integration_v1.py` pasa en verde localmente y en CI
- Workflow de CI Tests muestra ✅ en push a `v_docker_prod`
- Workflow de Docker Build muestra ✅ en push a `v_docker_prod`
- Ningún dato de prueba queda sucio en Supabase (cleanup funciona)
