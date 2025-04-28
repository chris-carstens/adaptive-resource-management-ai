#!/bin/bash
echo "2. Setting up local registry..."
# Skip local registry for multi-node setup
# docker stop registry || true
# docker rm registry || true
# docker run -d -p 5000:5000 --name registry registry:2

echo "3. Building and pushing Docker images..."
docker build -t flask-app1:latest -f Dockerfile-app1 .
docker build -t flask-app2:latest -f Dockerfile-app2 .
docker build -t flask-app-gateway:latest -f Dockerfile-gateway .

# Use 127.0.0.1:5000 instead of localhost:5000 to avoid IPv6 issues
docker tag flask-app1:latest 192.168.49.2:5000/flask-app1:latest
docker tag flask-app2:latest 127.0.0.1:5000/flask-app2:latest
docker tag flask-app-gateway:latest 127.0.0.1:5000/flask-app-gateway:latest

docker push 192.168.49.2:5000/flask-app1:latest
docker push 127.0.0.1:5000/flask-app2:latest
docker push 127.0.0.1:5000/flask-app-gateway:latest

echo "4. Applying RBAC configuration..."
kubectl apply -f rbac.yaml

echo "5. Deploying to Kubernetes..."
kubectl apply -f flask-app.yaml
