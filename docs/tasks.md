# Task Board: OrganizaT

> **Basado en:** init-pipeline (proyecto existente)  
> **Total de tasks:** 10 completadas + 7 pendientes

---

## 🐳 Tasks Docker + Kubernetes (CR-001)
> Nuevas tasks derivadas del CR-001 — contenerización y deploy en K8s con Helm + Minikube.
> Ver detalle completo en `docs/changes/CR-001-docker-kubernetes.md`.

- [x] **TASK-010** — Crear ramas `v_docker_dev` y `v_docker_prod` desde `production`
  - **Estado:** ✅ completado
  - **Archivos principales:** git (solo operación de ramas)
  - **Notas:** Ambas ramas creadas y pusheadas a origin. `v_docker_dev` es la rama de trabajo; `v_docker_prod` recibirá el merge cuando esté validado.

- [x] **TASK-011** — Crear `Dockerfile` y `.dockerignore`
  - **Estado:** ✅ completado
  - **Descripción:** Contenerizar la app FastAPI usando `python:3.12-slim` como base. Entrypoint con uvicorn en `0.0.0.0:8000`. Variables de entorno inyectadas en runtime (no desde `.env`).
  - **Archivos involucrados:** `Dockerfile`, `.dockerignore`
  - **Depende de:** TASK-010
  - **Criterio de done:** `docker build -t organizat-api .` termina sin errores; imagen levanta y `/health` responde OK.
  - **Notas:** Validado con `docker build` y `docker run` usando `--env-file`; `/health` responde `{"status":"ok","supabase_connected":true}`.

- [x] **TASK-012** — Validar build y run local con Docker
  - **Estado:** ✅ completado
  - **Descripción:** Buildear imagen, correr contenedor inyectando `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` como env vars, validar que la API responde correctamente.
  - **Archivos involucrados:** `Dockerfile`, `.dockerignore`
  - **Depende de:** TASK-011
  - **Criterio de done:** `docker run` levanta la API; `curl localhost:8000/health` devuelve `{"status": "ok"}`.
  - **Notas:** La inyección de variables funcionó con `--env-file` y la conexión a Supabase quedó activa.

- [x] **TASK-013** — Crear Helm chart (`helm/`)
  - **Estado:** ✅ completado
  - **Descripción:** Chart con Deployment, Service, Secret y ConfigMap. Solo `values-dev.yaml` para Minikube — `values-prod.yaml` fuera del scope de esta entrega. Liveness/readiness probes apuntan a `/health`.
  - **Archivos involucrados:** `helm/Chart.yaml`, `helm/values.yaml`, `helm/values-dev.yaml`, `helm/templates/deployment.yaml`, `helm/templates/service.yaml`, `helm/templates/secret.yaml`, `helm/templates/configmap.yaml`, `helm/templates/_helpers.tpl`, `helm/templates/NOTES.txt`
  - **Depende de:** TASK-010
  - **Criterio de done:** `helm lint helm/` pasa sin errores; `helm template` genera manifiestos K8s válidos.
  - **Notas:** Mantener el scope mínimo: backend, Minikube y Helm; no agregar extras de cloud todavía.
  - **Notas:** Las variables Supabase para Helm se inyectan desde `values-dev.yaml` y se traducen a un `Secret` con `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL`, `ANON_KEY` y `SERVICE_ROLE` para validar el despliegue en Minikube.

- [x] **TASK-014** — Desplegar y validar en Minikube local
  - **Estado:** ✅ completado
  - **Descripción:** Levantar Minikube, buildear imagen en el contexto Docker de Minikube (`eval $(minikube docker-env)`), instalar Helm chart con values-dev y validar que el pod queda Running.
  - **Archivos involucrados:** `scripts/minikube-setup.sh`, `helm/organizat/values-dev.yaml`
  - **Depende de:** TASK-012, TASK-013
  - **Criterio de done:** `kubectl get pods` muestra pod en estado `Running`; liveness y readiness probes pasan; endpoint accesible desde host via port-forward.
  - **Notas:** Validado en Minikube con `helm upgrade --install`, `kubectl rollout status`, `kubectl exec` para verificar env vars y `curl /health` con `supabase_connected:true`.

- [x] **TASK-015** — Actualizar docs del pipeline y mergear a `v_docker_prod`
  - **Estado:** ✅ completado
  - **Descripción:** Actualizar `project-brief.md`, `design.md`, `blueprint.md` y `CR-001` con el estado final. Merge de `v_docker_dev` → `v_docker_prod` una vez validado.
  - **Archivos involucrados:** `docs/project-brief.md`, `docs/design.md`, `docs/blueprint.md`, `docs/tasks.md`, `docs/changes/CR-001-docker-kubernetes.md`
  - **Notas:** Docs actualizados. Minikube validado: pod Running, /health responde `{"status":"ok","supabase_connected":true}`.

---

## Orden de ejecución

### Rama: `v_docker_dev` / `v_docker_prod` — Docker + Kubernetes (CR-001)
> El backlog funcional (TASK-001 a TASK-009) vive en las ramas `development` / `production`.
> En esta rama nos enfocamos exclusivamente en infra de deployment.

1. `TASK-010` ✅ — Ramas creadas.
2. `TASK-011` ✅ — Dockerfile + .dockerignore.
3. `TASK-012` ✅ — Validar Docker local.
4. `TASK-013` ✅ — Helm chart completo.
5. `TASK-014` ✅ — Deploy y validación en Minikube.
6. `TASK-015` — Docs actualizados + merge a `v_docker_prod`.

---

Notas:
- El backlog funcional (TASK-001 a TASK-009, incluyendo IMPL-001 a IMPL-008) está documentado
  en las ramas `development` y `production`. Esta rama se limita a CR-001.