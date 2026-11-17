#!/bin/sh
set -eu

: "${BUILD_NUMBER:?Build number is required}"
: "${K8S_TOKEN:?Kubernetes token is required}"
: "${K8S_CA:?Kubernetes CA certificate is required}"

IMAGE="abc-retail-app:${BUILD_NUMBER}"

k() {
    kubectl \
      --server="https://kubernetes:54815" \
      --certificate-authority="$K8S_CA" \
      --token="$K8S_TOKEN" "$@"
}

echo "Importing Docker image into Kubernetes..."
docker save "$IMAGE" | docker exec -i desktop-control-plane \
  ctr -n k8s.io images import -

echo "Applying Kubernetes Service..."
k apply -f kubernetes/service.yaml

echo "Deploying application version ${BUILD_NUMBER}..."
sed "s|image: abc-retail-app:1.0|image: $IMAGE|" \
  kubernetes/deployment.yaml | k apply -f -

echo "Checking deployment rollout..."
k rollout status deployment/abc-retail-app \
  --namespace default --timeout=180s

echo "Kubernetes deployment completed successfully."
