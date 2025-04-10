# Step 4: Build and Push Docker Images
echo "Building and pushing Docker images..."
docker build -t flask-app1:latest -f Dockerfile-app1 .
docker build -t flask-app2:latest -f Dockerfile-app2 .

docker tag flask-app1:latest localhost:5000/flask-app1:latest
docker tag flask-app2:latest localhost:5000/flask-app2:latest

docker push localhost:5000/flask-app1:latest
docker push localhost:5000/flask-app2:latest

# Step 6: Apply RBAC Configuration
echo "Applying RBAC configuration..."
kubectl apply -f rbac.yaml

# Step 7: Deploy to Kubernetes
echo "Deploying to Kubernetes..."
kubectl apply -f flask-app.yaml

# For subsequent updates (only if deployment exists)
kubectl rollout restart deployment flask-app-1
kubectl rollout restart deployment flask-app-2

echo "Deployment restarted successfully."
minikube service flask-app-1-service --url
