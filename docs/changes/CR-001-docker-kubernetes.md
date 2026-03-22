# CR-001: Contenerización Docker + Deploy Kubernetes (Helm + Minikube)

> **Tipo:** 🔴 LARGE
> **Fecha:** 2026-03-21
> **Estado:** 🔄 En progreso — pendiente aprobación de implementación
> **Ramas:** `v_docker_dev` (trabajo) → `v_docker_prod` (estable)

---

## Descripción del cambio

Agregar infraestructura Docker + Kubernetes al backend OrganizaT para poder desplegarlo
en un cluster K8s, administrado con **Helm** y validado localmente con **Minikube**.

El cambio NO modifica ningún endpoint, modelo ni lógica de negocio. Es un cambio exclusivamente
de infraestructura y deployment.

### Qué se agrega
- `Dockerfile` para contenerizar la app FastAPI con uvicorn
- `.dockerignore` para excluir archivos innecesarios del build
- Helm chart en `helm/organizat/` para administrar el despliegue en Kubernetes
- Script `scripts/minikube-setup.sh` para levantar el entorno local completo

### Qué se mantiene (solo en `production` y `development`)
- Toda la lógica del API (`*/api.py`, `*/schemas.py`, `main.py`, `database.py`) sin cambios


### Fuera del scope de esta entrega
- `values-prod.yaml` — se agrega cuando se defina el proveedor cloud (GKE, EKS, etc.)
- Configuración de registry de imágenes externo (Docker Hub, GCR, ECR)
- Integración con External Secrets Operator — no aplica para entrega académica

---

## Motivación

El backend necesita desplegarse en Kubernetes junto con el frontend (repo separado) en un
cluster compartido. El objetivo de esta entrega es:

1. Controlar versiones del deployment con Git (ramas dedicadas `v_docker_*`)
2. Contenerizar la aplicación con Docker (`Dockerfile` es suficiente)
3. Desplegar en Kubernetes administrado con Helm
4. Probar y validar todo localmente con Minikube — el ajuste al cloud viene después
5. Limpiar el código/documentación de restos de Vercel que ya no sean necesarios

---

## Estrategia de ramas

```
production (base)
    ├── v_docker_dev   ← rama de trabajo (implementación y pruebas)
    └── v_docker_prod  ← rama estable (merge desde v_docker_dev cuando esté validado)
```

Notas:
- Los merges de features del API siguen su propio track: `development` → `production`
- Ambos tracks son completamente independientes
- Antes de arrancar TASK-011, limpiar referencias a Vercel y decidir el destino de `api_test_log.json`

---

## Impacto estimado

### Documentos a actualizar
- [x] `docs/project-brief.md` — deploy target alternativo, branching strategy ✅
- [x] `docs/design.md` — sección de arquitectura Docker + Helm + K8s ✅
- [x] `docs/blueprint.md` — riesgos del nuevo stack de infra ✅
- [x] `docs/tasks.md` — TASK-010 a TASK-015 ✅

### Tasks del CR en `docs/tasks.md`

- [x] **TASK-010** — Crear ramas `v_docker_dev` y `v_docker_prod` desde `production` ✅
- [ ] **TASK-011** — Crear `Dockerfile` y `.dockerignore`
- [ ] **TASK-012** — Validar build y run local con Docker
- [ ] **TASK-013** — Crear Helm chart (`helm/organizat/`)
  - **Notas:** Mantener el scope mínimo: backend, Minikube y Helm; no agregar extras de cloud todavía.
- [ ] **TASK-014** — Desplegar y validar en Minikube local
- [ ] **TASK-015** — Merge `v_docker_dev` → `v_docker_prod`

### Archivos a crear (cuando se apruebe implementación)

| Archivo | Propósito |
|---------|-----------|
| `Dockerfile` | Build de la imagen de la app FastAPI |
| `.dockerignore` | Excluir `venv/`, `.env*`, `__pycache__/`, `*.pyc`, `tests/`, `docs/`, `.git/` |
| `helm/organizat/Chart.yaml` | Metadata del chart (nombre, versión, descripción) |
| `helm/organizat/values.yaml` | Valores default (imagen, puerto 8000, replicas, recursos) |
| `helm/organizat/values-dev.yaml` | Override Minikube: `imagePullPolicy: Never`, replicas 1 |
| `helm/organizat/templates/_helpers.tpl` | Helpers estándar de Helm (fullname, labels) |
| `helm/organizat/templates/deployment.yaml` | K8s Deployment con liveness/readiness en `/health` |
| `helm/organizat/templates/service.yaml` | K8s Service — NodePort en dev |
| `helm/organizat/templates/secret.yaml` | K8s Secret para SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY |
| `helm/organizat/templates/configmap.yaml` | K8s ConfigMap para config no sensible |
| `helm/organizat/templates/NOTES.txt` | Instrucciones post-install del chart |
| `scripts/minikube-setup.sh` | Script que levanta Minikube, buildea imagen e instala el chart |

### Archivos de código modificados

**Ninguno.** La lógica del API no cambia.

---

## Decisiones técnicas

### Dockerfile
- **Base image:** `python:3.12-slim` — ligera, sin extras innecesarios
- **Multi-stage build:** NO — no hay step de compilación pesada; un solo stage es suficiente
- **Entrypoint:** `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1`
- **Puerto expuesto:** `8000`
- **Variables de entorno:** inyectadas en runtime desde K8s Secrets — no se usa `.env` en el contenedor
  - `database.py` ya tiene fallback a env vars del sistema → compatible sin cambios

### Helm chart
- **Liveness probe:** `GET /health` — endpoint ya existe en la API
- **Readiness probe:** `GET /health` — mismo endpoint
- **Secrets:** K8s Secrets separados — nunca en `values.yaml`; se pasan al instalar el chart con `--set`
- **values-dev.yaml:** `imagePullPolicy: Never` para usar imagen local en Minikube sin registry externo
- **values-prod.yaml:** NO en esta entrega — se agrega cuando se defina el proveedor cloud

### Minikube
- Contexto Docker de Minikube para buildear la imagen directamente (`eval $(minikube docker-env)`)
- Script `scripts/minikube-setup.sh` automatiza el flujo completo para reproducibilidad

---

## Riesgos

| # | Riesgo | Severidad | Mitigación |
|---|--------|-----------|-----------|
| 1 | Secrets en `values.yaml` o commiteados en repo | 🔴 Alto | Usar K8s Secrets; inyectar con `--set` al instalar; agregar `secrets.local.yaml` a `.gitignore` |
| 2 | Imagen Docker pesada | 🟡 Medio | `python:3.12-slim` + `.dockerignore` agresivo |
| 3 | `python-dotenv` busca `.env` inexistente en container | 🟢 Bajo | `database.py` ya maneja el fallback a env vars del sistema; no es bloqueante |
| 4 | Puerto bloqueado o conflicto en Minikube local | 🟢 Bajo | Documentar port-forward en `scripts/minikube-setup.sh` |

---

## Plan de ejecución

```
Paso 1: ✅ Crear ramas v_docker_dev y v_docker_prod          (TASK-010 — hecho)
Paso 2: ✅ Documentar el CR y actualizar docs/               (TASK-015 parcial — hecho)
Paso 3: [GATE] Aprobación de implementación por Andres
Paso 4: Crear Dockerfile + .dockerignore                     (TASK-011)
Paso 5: Validar build y run Docker local                     (TASK-012)
Paso 6: Crear Helm chart                                     (TASK-013)
Paso 7: Desplegar y validar en Minikube                      (TASK-014)
Paso 8: Merge v_docker_dev → v_docker_prod                   (TASK-015)
```

---

## Criterio de done

- [ ] `docker build -t organizat-api .` termina sin errores
- [ ] `docker run` con env vars inyectadas levanta la API; `GET /health` responde `{"status": "ok"}`
- [ ] `helm lint helm/organizat` pasa sin errores
- [ ] `helm install organizat ./helm/organizat -f helm/organizat/values-dev.yaml --set ...` en Minikube completa exitosamente
- [ ] `kubectl get pods` muestra pod en estado `Running`
- [ ] Liveness y readiness probes pasan (pod no entra en CrashLoop)
- [ ] Endpoint accesible desde el host via port-forward
- [ ] Merge de `v_docker_dev` → `v_docker_prod` realizado

---

## Notas

- `values-prod.yaml` se agrega en un CR posterior cuando se defina el proveedor cloud.
- El frontend (repo separado) se unirá al mismo cluster en una etapa posterior — el Helm chart
  de este CR es solo para el backend.
- `vercel.json` permanece en `production` y `development`; no existe en las ramas `v_docker_*`.