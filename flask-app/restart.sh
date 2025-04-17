#!/bin/bash
echo "1. Building and pushing Docker images..."
docker build -t flask-app1:latest -f Dockerfile-app1 .
docker build -t flask-app2:latest -f Dockerfile-app2 .
docker build -t flask-app-gateway:latest -f Dockerfile-gateway .

docker tag flask-app1:latest localhost:5000/flask-app1:latest
docker tag flask-app2:latest localhost:5000/flask-app2:latest
docker tag flask-app-gateway:latest localhost:5000/flask-app-gateway:latest

docker push localhost:5000/flask-app1:latest
docker push localhost:5000/flask-app2:latest
docker push localhost:5000/flask-app-gateway:latest

echo "2. Applying RBAC configuration..."
kubectl apply -f rbac.yaml

echo "3. Updating Kubernetes deployments..."
kubectl apply -f flask-app.yaml

echo "4. Restarting deployments..."
kubectl rollout restart deployment flask-app-1
kubectl rollout restart deployment flask-app-2
kubectl rollout restart deployment api-gateway

echo "5. Waiting for restart to complete..."
kubectl rollout status deployment/flask-app-1
kubectl rollout status deployment/flask-app-2
kubectl rollout status deployment/api-gateway

echo "Deployment restarted successfully."
GATEWAY_URL=$(minikube service api-gateway-service --url | head -n 1)
echo "API Gateway is accessible at: $GATEWAY_URL"
