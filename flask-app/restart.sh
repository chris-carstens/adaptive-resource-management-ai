#!/bin/bash
echo "1. Building Docker images directly in Minikube's Docker daemon..."
minikube image build -t flask-app1:latest -f Dockerfile-app1 . --all
minikube image build -t flask-app2:latest -f Dockerfile-app2 . --all
minikube image build -t flask-app-gateway:latest -f Dockerfile-gateway . --all

echo "2. Applying RBAC configuration..."
kubectl apply -f rbac.yaml

echo "3. Updating Kubernetes deployments..."
kubectl apply -f flask-app.yaml

echo "4. Restarting deployments..."
kubectl rollout restart deployment flask-app-1
kubectl rollout restart deployment flask-app-2
kubectl rollout restart deployment api-gateway

helm upgrade prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
