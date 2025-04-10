#!/bin/bash
echo "2. Configuring Docker environment..."
eval $(minikube docker-env)

echo "3. Setting up local registry..."
docker stop registry || true
docker rm registry || true
docker run -d -p 5000:5000 --name registry registry:2

echo "4. Building and pushing Docker images..."
cd flask-app
docker build -t flask-app1:latest -f Dockerfile-app1 .
docker build -t flask-app2:latest -f Dockerfile-app2 .

docker tag flask-app1:latest localhost:5000/flask-app1:latest
docker tag flask-app2:latest localhost:5000/flask-app2:latest

docker push localhost:5000/flask-app1:latest
docker push localhost:5000/flask-app2:latest

echo "6. Applying RBAC configuration..."
kubectl apply -f rbac.yaml

echo "7. Deploying to Kubernetes..."
kubectl apply -f flask-app.yaml

echo "Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=flask-app-1 --timeout=120s
kubectl wait --for=condition=ready pod -l app=flask-app-2 --timeout=120s

echo "Setup complete! You can check the status with:"
