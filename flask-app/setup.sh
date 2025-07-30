#!/bin/bash
echo "1. Building Docker images directly in Minikube's Docker daemon..."
minikube image build -t flask-app1:latest -f Dockerfile-app1 . --all
minikube image build -t flask-app2:latest -f Dockerfile-app2 . --all
minikube image build -t flask-app-gateway:latest -f Dockerfile-gateway . --all

echo "2. Applying RBAC configuration..."
kubectl apply -f rbac.yaml

echo "3. Deploying to Kubernetes..."
kubectl apply -f flask-app.yaml

# Prometheus setup
kubectl create namespace monitoring

helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set grafana.enabled=false \
  --set alertmanager.enabled=false

kubectl label pods -l app=flask-app-1 monitoring=true
kubectl label pods -l app=flask-app-2 monitoring=true

kubectl get pods -n monitoring

# Loki setup
kubectl apply -f loki-config.yaml
kubectl apply -f loki-deployment.yaml