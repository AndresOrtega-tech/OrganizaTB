# Blueprint: OrganizaT — estado, riesgos y ambigüedades

> **Última actualización:** 2026-03-21 — CR-001 aplicado (Docker + Kubernetes)

<!-- inferido del código -->
Este documento combina lo encontrado en el código (spec + diseño actual) y las decisiones/confirmaciones entregadas por el equipo. Su objetivo es servir como guía rápida de riesgos técnicos, mitigaciones y ambigüedades que requieren decisiones antes de promover cambios a producción.

---

## 1. Resumen ejecutivo

- Proyecto: OrganizaT — Backend (FastAPI) con Supabase (Auth + PostgreSQL). <!-- inferido del código -->
- Estado actual: API funcional con módulos: Auth, Tags, Tasks, Notes, Events, Reminders, Relations. RLS en la BD existe pero actualmente desactivado en el entorno de desarrollo. <!-- inferido del código --> <!-- confirmado por Andres -->
- Deploy objetivo actual: Vercel (configurado con `main.py` como entry). <!-- inferido del código -->
- Deploy alternativo en progreso: Docker + Kubernetes con Helm y Minikube — ver CR-001. <!-- CR-001 -->
- Ramas de infra: `v_docker_dev` (trabajo) → `v_docker_prod` (estable). <!-- CR-001 -->

---

## 2. Principales hallazgos de diseño y decisiones actuales

- Arquitectura: FastAPI app que incluye routers por módulo; supabase-py usado como cliente para Auth y Base de Datos; env vars cargadas por `python-dotenv`. Health endpoints y routers centralizados en `main.py`. <!-- inferido del código -->
- Modelo de datos: tablas principales en `database.txt` / migraciones `supabase/migrations/*`. Se usan joins en las queries para traer etiquetas y relaciones. <!-- inferido del código -->
- Autenticación: delegada a Supabase Auth; el backend usa `supabase.auth.*` para sign_up, sign_in, refresh, get_user. `get_current_user` valida tokens usando supabase client. <!-- inferido del código -->
- Reminders: se generan desde Tasks y Events (cálculo `remind_at = due_date/start_time - offset`). Estado `pending|sent|failed`. No hay worker implementado en este repo. <!-- inferido del código --> <!-- confirmado por Andres -->
- RLS: habilitado en scripts SQL, pero en práctica está desactivado en el entorno (confirmado). Esto tiene implicaciones de seguridad. <!-- inferido del código --> <!-- confirmado por Andres -->

---

## 3. Riesgos identificados (priorizados)

1. RLS desactivado en el entorno (Alto)
   - Impacto: lectura/escritura no restringida por usuario; mayor riesgo de exposición de datos entre usuarios.
   - Evidencia: `database.txt` habilita RLS y README/commits indican manejo, pero la configuración actual se confirma como desactivada. <!-- inferido del código --> <!-- confirmado por Andres -->
   - Mitigación inmediata: mantener RLS desactivado solo en entornos locales/ci, activar en staging/production después de probar políticas con usuarios de prueba. Crear un checklist de activación que incluya tests e2e.

2. Secret management — supabase keys en variables de entorno (Medio)
   - Impacto: claves sensibles cargadas desde `.env`; si se filtra `.env` o se imprime accidentalmente, hay riesgo de acceso.
   - Evidencia: `database.py` lee `SUPABASE_SERVICE_ROLE_KEY`/`SUPABASE_URL`; health endpoint devuelve `supabase_url` en `/health`. <!-- inferido del código -->
   - Mitigación inmediata: eliminar salida de `supabase_url` del health endpoint en producción; usar secret manager (Vercel secrets, Railway secret envs, or HashiCorp Vault) y rotación periódica.

3. CORS configurado con `"*"` (Medio → Alto en producción)
   - Impacto: permitir orígenes indefinidos facilita exfiltración cross-origin si hay XSS en clientes.
   - Evidencia: `main.py` permite `origins = ["*", ...]`. <!-- inferido del código -->
   - Mitigación: restringir `allow_origins` en producción a dominios permitidos (frontends oficiales) y activar revisión en CI/CD.

4. Falta de worker para recordatorios (Medio)
   - Impacto: estado `pending/sent/failed` nunca será consumido si no hay process que envíe notificaciones; inconsistencia en UX.
   - Evidencia: Reminders se insertan en BD pero no hay servicio en repo que los procese. <!-- inferido del código --> <!-- confirmado por Andres -->
   - Mitigación/Plan: definir arquitectura del worker (cron + queue o background worker en same repo), implementar un pequeño servicio que lea próximos reminders y cambie estado; documentar SLA (ej: enviar con 1 minuto de retraso máximo).

5. Operaciones parcialmente atómicas al crear usuario (Medio)
   - Impacto: si `supabase.auth.sign_up` crea el usuario en Auth pero la inserción/upsert del profile falla, el usuario quedará en Auth sin perfil. 
   - Evidencia: `auth/api.py` hace sign_up y luego upsert en `profiles` sin transacción ni rollback del auth. <!-- inferido del código -->
   - Mitigación: implementar compensating action (borrar usuario si falla la creación de perfil) o diseñar flujo en que el trigger de Supabase garantice la creación del perfil.

6. Constraints / checks pendientes en BD (Medio)
   - Impacto: reminders pueden referenciar tanto task_id como event_id o ninguno; integridad no garantizada.
   - Evidencia: `database.txt` menciona pendiente check `(task_id IS NOT NULL) XOR (event_id IS NOT NULL)`. Migración pendiente. <!-- inferido del código -->
   - Mitigación: aplicar migración que agregue el constraint en staging, validar con tests de integridad.

9. Secrets expuestos en Helm values o repo (Alto — CR-001)
   - Impacto: `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` nunca deben estar en `values.yaml` ni commiteados en el repo.
   - Evidencia: nueva infra Docker/K8s requiere K8s Secrets para inyectar credenciales. <!-- CR-001 -->
   - Mitigación: usar K8s Secrets separados al instalar el chart; agregar entradas al `.gitignore` para archivos de secrets locales.

10. Imagen Docker pesada / build lento (Medio — CR-001)
    - Impacto: builds lentos en CI y pulls lentos en K8s si la imagen no está optimizada.
    - Mitigación: base `python:3.12-slim` + `.dockerignore` agresivo (excluir `venv/`, `.env`, `tests/`, `docs/`, `.git/`, `__pycache__/`).

11. Diferencia de comportamiento Vercel (serverless) vs Docker (proceso continuo) (Medio — CR-001)
    - Impacto: Vercel ejecuta cada request en una función efímera; Docker/K8s corre uvicorn como proceso continuo — lifecycle distinto.
    - Mitigación: health check en `/health` como validación; smoke tests tras deploy en Minikube.

12. Minikube ≠ cloud real (networking, storage, ingress diferentes) (Medio — CR-001)
    - Impacto: lo que funciona en Minikube puede necesitar ajustes al cambiar a GKE/EKS/AKS.
    - Mitigación: Helm chart portable con `values-prod.yaml` separado (placeholder hasta definir proveedor).

13. `python-dotenv` en container sin `.env` (Bajo — CR-001)
    - Impacto: en el contenedor Docker no existirá `.env`; `python-dotenv` intenta cargarlo pero no es bloqueante.
    - Evidencia: `database.py` ya tiene fallback a variables de sistema operativo — no hay impacto real. <!-- inferido del código -->

7. Documentación desincronizada (Bajo → Medio)
   - Impacto: archivos `rules.md` y `docs/*` pueden no reflejar el código actual (ej. events ya terminado).
   - Evidencia: `events` ya se considera terminado en código pero `rules.md` apuntaba a refactorización; commits recientes añadieron `docs/ARCHITECTURE.md` y `docs/SPECS.md`. <!-- inferido del código --> <!-- confirmado por Andres -->
   - Mitigación: sincronizar docs, conservar changelog y exigir PRs con docs actualizadas.

8. Posible exposición de información por health endpoint (Bajo → Medio)
   - Impacto: `/health` devuelve `supabase_url` y `supabase_connected` — información sensible.
   - Mitigación: limitar health info en producción (solo status booleano), mover información detallada a endpoint protegido / interno.

---

## 4. Ambigüedades sin resolver / TODOs (pendientes de confirmación)

- Estado exacto de RLS en los entornos (staging/production): aunque confirmaste que está desactivado, necesitamos saber el plan de activación (fecha/owner). <!-- TODO: verificar -->
- Política de gestión de secrets en Vercel/production: ¿usar Vercel secrets o un vault central? <!-- TODO: verificar -->
- Arquitectura del worker para reminders: ¿se implementa como servicio dentro de este repo, o como micro-servicio separado? ¿Qué tecnología prefieren (Celery, RQ, cron+function, serverless)? <!-- TODO: verificar -->
- Responsable de QA para la activación de RLS y validación de políticas: ¿quién hará la verificación final? <!-- TODO: verificar -->
- Proceso de rollback para creación de usuarios cuando la creación del profile falla: ¿prefieren compensating action (borrar auth user) o aceptar usuarios huérfanos y arreglar con job? <!-- TODO: verificar -->
- Cobertura de tests: falta un resumen de qué pruebas end-to-end se ejecutarán antes del merge a production. <!-- TODO: verificar -->
- **CR-001** — Proveedor cloud final para K8s (GKE, EKS, AKS, DigitalOcean, etc.) aún por definir. `values-prod.yaml` es placeholder. <!-- TODO: verificar -->
- **CR-001** — Definir estrategia de registry de imágenes Docker (Docker Hub, GCR, ECR) para cuando se pase a cloud real. <!-- TODO: verificar -->
- **CR-001** — Confirmar si se necesita Ingress controller en Minikube local (nginx-ingress addon) o basta con port-forward para pruebas. <!-- TODO: verificar -->

---

## 5. Recomendaciones concretas (pasos accionables)

Prioridad alta (hacer antes de merge a `production` si procede):
1. Verificar que los cambios en `development` son solo documentales (hacer `git diff --name-only production..development` y revisar cada archivo de docs). <!-- confirmado por Andres -->
2. Ejecutar test suite y un smoke test local (`uvicorn main:app --reload` + health + login + create/list tasks). Agregar un job CI que ejecute esos tests. 
3. Remover `supabase_url` de la respuesta de `/health` en producción y limitar info sensible.
4. Cambiar `CORS` para producción a la lista explícita de orígenes del frontend (remover `"*"`).
5. Aplicar migración pendiente para `reminders` check constraint en staging y validar integridad.
6. Planificar e implementar worker de reminders con pruebas básicas (env var para activar/desactivar).
7. Agregar control de errores y compensating action en `auth` para evitar usuarios huérfanos (o documentar por qué no es necesario).

Prioridad media:
1. Revisar manejo de errores en puntos donde se captura excepción genérica y se oculta la causa (añadir logs estructurados y códigos de error).
2. Añadir documentación operativa (playbook) para activar RLS: pasos, pruebas y rollback.
3. Añadir linting y pre-commit hooks para evitar commits accidentales de `.env` y archivos sensibles.

Prioridad baja:
1. Completar `TagUpdate` para exponer `icon` si se desea editar desde API (hay inconsistencia entre schema y DB). <!-- inferido del código -->
2. Revisar y consolidar `docs/ARCHITECTURE.md` y `docs/SPECS.md` con `rules.md` para evitar duplicidad.

---

## 6. Plan seguro para actualizar docs y merge a production (sugerencia)

1. En `development`:
   - Actualizar solamente archivos en `docs/` y `README.md`.
   - Ejecutar test suite local y CI (si existe).
   - Revisar diff: confirmar que `git status` muestra sólo cambios de docs. (Si aparece algún archivo de código modificado, revertir o mover a PR separado.)
2. Push a `development` y abrir PR con descripción: "Solo documentación — no cambios de comportamiento". Incluir checklist:
   - [ ] Tests unitarios pasan
   - [ ] Smoke tests (login, create task, list task) pasan
   - [ ] No cambios en código fuente (listar `git diff --name-only production..development`)
3. Merge a `production` desde la UI o con `git merge --no-ff development` tras aprobación.
4. Después del merge: ejecutar pipeline de staging/production (si aplica) y correr smoke tests en producción.
5. Activar cualquier cambio de configuración sensible (CORS, secrets) tras validación.

---

## 7. Riesgos residuales y seguimiento

- Riesgo residual: sin worker activo los reminders se acumulan en DB. Planear prioridad de implementación en próximos sprints. <!-- confirmado por Andres -->
- Seguimiento: documentar responsables por cada mitigación (RLS, worker, secrets). Añadir tasks en `tasks.md` para que queden priorizados y asignados.

---

## 8. Ambigüedades marcadas en el código (`<!-- TODO: verificar -->`)

- Necesitamos verificar y cerrar las siguientes líneas en los documentos generados:
  - `<!-- TODO: verificar -->` — Estado final de RLS en staging/production.
  - `<!-- TODO: verificar -->` — Decisión arquitectónica sobre worker de reminders (ubicación/tecnología).
  - `<!-- TODO: verificar -->` — Política de gestión de secrets y rotación.
  - `<!-- TODO: verificar -->` — Procedimiento de rollback para creación de usuarios.

---

## 9. Change Requests aplicados a este blueprint

| CR | Tipo | Descripción | Estado |
|----|------|-------------|--------|
| [CR-001](changes/CR-001-docker-kubernetes.md) | 🔴 LARGE | Contenerización Docker + Deploy Kubernetes (Helm + Minikube) | 🔄 En progreso |

---

## 10. Conclusión

El sistema está funcional y bien organizado. Los principales bloqueos para una promoción segura a production son operativos y de seguridad (RLS, secrets, CORS, worker para reminders). En paralelo, se está implementando la infraestructura Docker + Kubernetes (CR-001) en las ramas `v_docker_dev` / `v_docker_prod`. Si quieres, puedo:

- Generar el PR-ready checklist y el mensaje de PR para la merge de docs a `production`.
- Añadir entradas concretas a `tasks.md` para cada mitigación (priorizadas).
- Proponer un diseño inicial para el worker de reminders (cron vs queue) y un plan de implementación mínimo viable.

<!-- inferido del código -->
<!-- confirmado por Andres -->