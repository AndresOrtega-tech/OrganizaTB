#!/usr/bin/env bash
# scripts/minikube-setup.sh
# Levanta Minikube, buildea la imagen del backend e instala el Helm chart del backend.
# Uso: bash scripts/minikube-setup.sh [--skip-minikube]

set -euo pipefail

# ── colores ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

step()  { echo -e "\n${BLUE}▶  $*${NC}"; }
ok()    { echo -e "${GREEN}✔  $*${NC}"; }
warn()  { echo -e "${YELLOW}⚠  $*${NC}"; }
error() { echo -e "${RED}✖  $*${NC}"; exit 1; }

# ── config ─────────────────────────────────────────────────────────────────────
IMAGE_NAME="organizat-api"
IMAGE_TAG="latest"
HELM_RELEASE="organizat-backend"
HELM_CHART="helm"
VALUES_DEV="helm/values-dev.yaml"
VALUES_LOCAL="helm/values-dev.local.yaml"
NAMESPACE="default"

# ── raíz del proyecto ──────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# ── 1. dependencias ────────────────────────────────────────────────────────────
step "1/7  Verificando dependencias"
for cmd in minikube docker helm kubectl; do
  command -v "$cmd" &>/dev/null || error "Falta '$cmd'. Instálalo antes de continuar."
done
ok "minikube / docker / helm / kubectl presentes"

# ── 2. values-dev.local.yaml ──────────────────────────────────────────────────
step "2/7  Verificando secrets locales"
[[ -f "$VALUES_LOCAL" ]] || error "No se encontró $VALUES_LOCAL — crea ese archivo con tus credenciales de Supabase."
ok "$VALUES_LOCAL encontrado"

# ── 3. Minikube ───────────────────────────────────────────────────────────────
SKIP_MINIKUBE="${1:-}"
step "3/7  Verificando Minikube"
if [[ "$SKIP_MINIKUBE" == "--skip-minikube" ]] && kubectl cluster-info &>/dev/null 2>&1; then
  ok "Cluster accesible — omitiendo minikube start"
else
  if [[ "$SKIP_MINIKUBE" == "--skip-minikube" ]]; then
    warn "API server no responde con --skip-minikube — ejecutando minikube start de todas formas"
  fi
  minikube start --base-image="gcr.io/k8s-minikube/kicbase:v0.0.50"
  ok "Minikube listo"
fi

# ── 3b. sincronizar contexto kubectl → siempre ────────────────────────────────
minikube update-context &>/dev/null
ok "kubectl context → minikube"

# ── 4. Docker → daemon de Minikube ────────────────────────────────────────────
step "4/7  Apuntando Docker al daemon de Minikube"
eval "$(minikube docker-env)"
ok "Docker context → Minikube"

# ── 5. build ──────────────────────────────────────────────────────────────────
step "5/7  Construyendo imagen ${IMAGE_NAME}:${IMAGE_TAG}"
docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .
ok "Imagen ${IMAGE_NAME}:${IMAGE_TAG} lista"

# ── 6. helm upgrade --install ─────────────────────────────────────────────────
step "6/7  Instalando / actualizando Helm chart '${HELM_RELEASE}'"
helm upgrade --install "${HELM_RELEASE}" "${HELM_CHART}" \
  --namespace "${NAMESPACE}" \
  -f "${VALUES_DEV}" \
  -f "${VALUES_LOCAL}"
ok "Helm chart aplicado"

# ── 7. rollout ────────────────────────────────────────────────────────────────
step "7/7  Esperando rollout del deployment"
kubectl rollout status deployment/"${HELM_RELEASE}" \
  --namespace "${NAMESPACE}" \
  --timeout=120s
ok "Deployment listo"

# ── resumen ───────────────────────────────────────────────────────────────────
SERVICE_URL=$(minikube service "${HELM_RELEASE}" --url --namespace "${NAMESPACE}" 2>/dev/null || true)

echo ""
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Backend corriendo en Minikube ✔           ${NC}"
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo ""
kubectl get pods --namespace "${NAMESPACE}" \
  -l "app.kubernetes.io/instance=${HELM_RELEASE}"
echo ""
if [[ -n "$SERVICE_URL" ]]; then
  echo -e "  Servicio : ${BLUE}${SERVICE_URL}${NC}"
  echo -e "  Health   : ${BLUE}${SERVICE_URL}/health${NC}"
else
  echo -e "  ${YELLOW}Corre esto para obtener la URL del servicio:${NC}"
  echo -e "  ${BLUE}minikube service ${HELM_RELEASE} --url${NC}"
fi
echo ""
