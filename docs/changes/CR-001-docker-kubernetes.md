# CR-001: Contenerización Docker + Deploy Kubernetes (Helm + Minikube)

> **Tipo:** 🔴 LARGE
> **Fecha:** 2026-03-21
> **Estado:** 🔄 En progreso — pendiente aprobación de implementación
> **Ramas:** `v_docker_dev` (trabajo) → `v_docker_prod` (estable)

---

## Descripción del cambio

Migrar la estrategia de deploy del backend OrganizaT de Vercel (`@vercel/python`) a un enfoque
basado en **Docker + Kubernetes**, administrado con **Helm** y validado localmente con **Minikube**.

El cambio NO modifica ningún endpoint, modelo ni lógica de negocio. Es un cambio exclusivamente
de infraestructura y deployment.

### Qué se agrega
- `Dockerfile` para contenerizar la app FastAPI con uvicorn
- `.dockerignore` para excluir archivos innecesarios del build
- Helm chart completo en `helm/organizat/` para administrar el despliegue en Kubernetes
- Script `scripts/minikube-setup.sh` para levantar el entorno local completo

### Qué se mantiene
- `vercel.json` — el deploy en Vercel sigue siendo una opción válida en paralelo
- Toda la lógica del API (`*/api.py`, `*/schemas.py`, `main.py`, `database.py`) sin cambios

---

## Motivación

El backend necesita desplegarse en Kubernetes. El proveedor cloud final está por definir
(se decide después de validar localmente con Minikube). El objetivo es:

1. Controlar versiones del deployment con Git (ramas dedicadas `v_docker_*`)
2. Contenerizar la aplicación con Docker (un `Dockerfile` es suficiente)
3. Desplegar en Kubernetes administrado con Helm
4. Probar y validar todo localmente con Minikube antes de tocar ningún cloud

---

## Estrategia de ramas

```
production (base)
    ├── v_docker_dev   ← rama de trabajo (implementación y pruebas)
    └── v_docker_prod  ← rama estable (merge desde v_docker_dev cuando esté validado)
```

Flujo de trabajo:
- Todo el desarrollo Docker/K8s ocurre en `v_docker_dev`
- Cuando esté validado localmente con Minikube, se mergea a `v_docker_prod`
- `v_docker_prod` refleja la versión lista para desplegarse en cloud

---

## Impacto estimado

### Documentos a actualizar
- [ ] `docs/project-brief.md` — agregar Docker + K8s como deploy target alternativo; actualizar stack
- [ ] `docs/design.md` — nueva sección de arquitectura de deployment (Docker + Helm + K8s)
- [ ] `docs/blueprint.md` — agregar riesgos del nuevo stack de infra (secrets en K8s, probes, imagen)
- [ ] `docs/tasks.md` — agregar TASK-010 a TASK-015

### Tasks nuevas a agregar en docs/tasks.md

- [ ] **TASK-010** — Crear ramas `v_docker_dev` y `v_docker_prod` desde `production`
  - Descripción: crear las dos ramas desde `production` y pushearlas a origin
  - Archivos involucrados: solo git (sin archivos nuevos)
  - Depende de: ninguna
  - Criterio de done: ambas ramas existen en local y en origin ✅ (ya completado)

- [ ] **TASK-011** — Crear `Dockerfile` y `.dockerignore`
  - Descripción: contenerizar la app FastAPI usando `python:3.12-slim` como base; entrypoint con uvicorn
  - Archivos involucrados: `Dockerfile`, `.dockerignore`
  - Depende de: TASK-010
  - Criterio de done: `docker build -t organizat-api .` termina sin errores; imagen levanta correctamente

- [ ] **TASK-012** — Validar build y run local con Docker
  - Descripción: buildear imagen, correr contenedor con env vars inyectadas, validar que `/health` responde OK
  - Archivos involucrados: `Dockerfile`, `.dockerignore`
  - Depende de: TASK-011
  - Criterio de done: `docker run` levanta la API, `curl localhost:8000/health` devuelve `{"status": "ok"}`

- [ ] **TASK-013** — Crear Helm chart completo (`helm/organizat/`)
  - Descripción: chart con Deployment, Service, Secret, ConfigMap y valores separados para dev y prod
  - Archivos involucrados: `helm/organizat/Chart.yaml`, `values.yaml`, `values-dev.yaml`,
    `values-prod.yaml`, `templates/deployment.yaml`, `templates/service.yaml`,
    `templates/secret.yaml`, `templates/configmap.yaml`, `templates/_helpers.tpl`, `templates/NOTES.txt`
  - Depende de: TASK-010
  - Criterio de done: `helm lint helm/organizat` pasa sin errores; `helm template` genera manifiestos válidos

- [ ] **TASK-014** — Desplegar y validar en Minikube local
  - Descripción: levantar Minikube, buildear imagen en contexto de Minikube, instalar Helm chart y validar
  - Archivos involucrados: `scripts/minikube-setup.sh`, `helm/organizat/values-dev.yaml`
  - Depende de: TASK-012, TASK-013
  - Criterio de done: `kubectl get pods` muestra pod `Running`; liveness/readiness probes pasan;
    endpoint accesible desde host devuelve respuesta válida del API

- [ ] **TASK-015** — Actualizar docs del pipeline y hacer merge a `v_docker_prod`
  - Descripción: actualizar `project-brief.md`, `design.md`, `blueprint.md` con el nuevo stack;
    merge de `v_docker_dev` a `v_docker_prod` una vez validado
  - Archivos involucrados: `docs/project-brief.md`, `docs/design.md`, `docs/blueprint.md`, `docs/tasks.md`
  - Depende de: TASK-014
  - Criterio de done: docs actualizados; PR aprobado; `v_docker_prod` en sync con el estado validado

### Archivos nuevos a crear (cuando se apruebe implementación)

| Archivo | Propósito |
|---------|-----------|
| `Dockerfile` | Build de la imagen de la app FastAPI |
| `.dockerignore` | Excluir `venv/`, `.env`, `__pycache__`, `*.pyc`, `tests/`, `docs/`, `.git/` |
| `helm/organizat/Chart.yaml` | Metadata del chart (nombre, versión, descripción) |
| `helm/organizat/values.yaml` | Valores default (imagen, puerto 8000, replicas, recursos) |
| `helm/organizat/values-dev.yaml` | Override dev: `imagePullPolicy: Never`, replicas 1, Minikube |
| `helm/organizat/values-prod.yaml` | Override prod: placeholder hasta definir proveedor cloud |
| `helm/organizat/templates/_helpers.tpl` | Helpers estándar de Helm (fullname, labels) |
| `helm/organizat/templates/deployment.yaml` | K8s Deployment con liveness/readiness en `/health` |
| `helm/organizat/templates/service.yaml` | K8s Service tipo ClusterIP (NodePort en dev) |
| `helm/organizat/templates/secret.yaml` | K8s Secret para SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY |
| `helm/organizat/templates/configmap.yaml` | K8s ConfigMap para config no sensible |
| `helm/organizat/templates/NOTES.txt` | Instrucciones post-install del chart |
| `scripts/minikube-setup.sh` | Script que levanta Minikube, buildea imagen e instala el chart |

### Archivos de código modificados

**Ninguno.** La lógica del API no cambia. `vercel.json` se mantiene intacto.

---

## Decisiones técnicas

### Dockerfile
- **Base image:** `python:3.12-slim` — imagen oficial oficial ligera, sin extras innecesarios
- **Multi-stage build:** NO por ahora — no hay step de compilación pesada; la simplicidad es suficiente
- **Entrypoint:** `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1`
- **Puerto expuesto:** `8000`
- **Variables de entorno:** inyectadas en tiempo de ejecución desde K8s Secrets (no desde `.env`)
  - `python-dotenv` ya maneja el caso donde no existe `.env` (el fallback a vars de sistema está en `database.py`)

### Helm chart
- **Liveness probe:** `GET /health` — ya existe en la API
- **Readiness probe:** `GET /health` — mismo endpoint
- **Secrets:** K8s Secrets separados — nunca en `values.yaml`; se proveen al instalar el chart
- **values-dev.yaml:** `imagePullPolicy: Never` para usar imagen local en Minikube sin registry externo
- **values-prod.yaml:** placeholder — se completa cuando se defina el proveedor cloud (GKE, EKS, etc.)

### Minikube
- Contexto Docker de Minikube para buildear la imagen directamente sin registry externo
  (`eval $(minikube docker-env)` antes del `docker build`)
- Script `scripts/minikube-setup.sh` automatiza el flujo completo para onboarding rápido

### Branching Docker/K8s
- `v_docker_dev` — desarrollo activo y pruebas locales
- `v_docker_prod` — versión validada y lista para cloud (actúa como `production` para esta rama de infra)
- Los merges de features de negocio de `development` → `production` se hacen independientemente
  de este track de infra

---

## Riesgos

| # | Riesgo | Severidad | Mitigación |
|---|--------|-----------|-----------|
| 1 | Secrets expuestos en `values.yaml` o commiteados en repo | 🔴 Alto | Usar K8s Secrets; nunca poner valores sensibles en values files; agregar al `.gitignore` |
| 2 | Imagen Docker pesada (build lento, pull lento en K8s) | 🟡 Medio | `python:3.12-slim` + `.dockerignore` agresivo; no instalar deps de dev en imagen |
| 3 | Diferencia de comportamiento entre Vercel (serverless) y Docker (proceso continuo) | 🟡 Medio | Validar con health check + smoke tests en Docker antes de mergear |
| 4 | Minikube ≠ cloud real (networking, storage, ingress diferente) | 🟡 Medio | Helm chart portable con `values-prod.yaml` separado para ajustar sin cambiar templates |
| 5 | `python-dotenv` intenta cargar `.env` que no existirá en container | 🟢 Bajo | `database.py` ya maneja el fallback a env vars del sistema operativo correctamente |
| 6 | Puerto bloqueado o conflicto en Minikube local | 🟢 Bajo | Documentar en `scripts/minikube-setup.sh` los pasos de port-forward |

---

## Plan de ejecución

Re-entrada al pipeline desde: **Workflow 1 parcial + Workflow 2 completo (área de infra)**

```
Paso 1: ✅ Crear ramas v_docker_dev y v_docker_prod (TASK-010 — ya hecho)
Paso 2: ✅ Documentar el CR (este archivo + actualizar docs/)
Paso 3: [GATE] Aprobación de implementación por Andres
Paso 4: Implementar Dockerfile + .dockerignore (TASK-011)
Paso 5: Validar build y run Docker local (TASK-012)
Paso 6: Implementar Helm chart (TASK-013)
Paso 7: Validar en Minikube (TASK-014)
Paso 8: Actualizar docs + merge v_docker_dev → v_docker_prod (TASK-015)
```

---

## Criterio de done

El CR se considera completado cuando:

- [ ] `docker build -t organizat-api .` termina sin errores
- [ ] `docker run` levanta la API y `GET /health` responde `{"status": "ok"}`
- [ ] `helm lint helm/organizat` pasa sin errores ni warnings críticos
- [ ] `helm install organizat ./helm/organizat -f helm/organizat/values-dev.yaml` en Minikube
      completa exitosamente
- [ ] `kubectl get pods` muestra pod en estado `Running`
- [ ] Liveness y readiness probes pasan (pod no entra en CrashLoop)
- [ ] Un endpoint funcional del API es accesible desde el host (via port-forward o NodePort)
- [ ] Docs del pipeline actualizados (`project-brief.md`, `design.md`, `blueprint.md`, `tasks.md`)
- [ ] Merge de `v_docker_dev` → `v_docker_prod` realizado

---

## Notas adicionales

- El proveedor cloud final para K8s (GKE, EKS, AKS, DigitalOcean, etc.) se define en una etapa
  posterior. El `values-prod.yaml` quedará como placeholder hasta esa decisión.
- El deploy en Vercel **no se elimina** con este CR — `vercel.json` se mantiene.
  Ambas estrategias coexisten; la decisión de cuál usar en producción viene después.
- Los scripts en `scripts/` son opcionales para el CI pero necesarios para el onboarding local.