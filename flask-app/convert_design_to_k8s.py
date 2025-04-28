#!/usr/bin/env python3

import json
import yaml
import os
from collections import defaultdict


def load_design_time_json(filepath):
    """Load the design_time JSON file"""
    with open(filepath, 'r') as file:
        return json.load(file)


def map_layers_to_nodes(design_data):
    """Map computational layers to Kubernetes node names"""
    # Use the description field directly from VMs as node names
    node_mapping = {}
    for layer_name, vms in design_data["CloudResources"].items():
        for vm_name, vm_details in vms.items():
            if "description" in vm_details:
                node_mapping[vm_name] = vm_details["description"]
            else:
                # Fallback if description is not provided
                node_mapping[vm_name] = "minikube"
    
    return node_mapping


def create_deployments_from_components(design_data, component_map):
    """Create Kubernetes deployments based on components in design data"""
    deployments = []
    services = []
    
    # Map VM resources directly to their description (node names)
    resource_to_node = {}
    for layer_name, vms in design_data["CloudResources"].items():
        for vm_name, vm_details in vms.items():
            if "description" in vm_details:
                resource_to_node[vm_name] = vm_details["description"]
            else:
                resource_to_node[vm_name] = "minikube"  # Default fallback
    
    print("Resource to Node mapping:", resource_to_node)
    
    for comp_id, comp_config in component_map.items():
        if comp_id not in design_data["Components"]:
            continue
            
        # Get deployment name and standard image (without registry prefix)
        deployment_name = comp_config["name"]
        # Extract base image name without registry prefix
        image_name = comp_config["image"].split('/')[-1]
        
        # Find compatible resources
        compatible_resources = []
        if comp_id in design_data["CompatibilityMatrix"]:
            for hw_ver in design_data["CompatibilityMatrix"][comp_id]:
                compatible_resources.extend([entry["resource"] for entry in design_data["CompatibilityMatrix"][comp_id][hw_ver]])
        
        # Map resources to node names
        compatible_nodes = ["minikube"]  # Default fallback
        for resource in compatible_resources:
            if resource in resource_to_node:
                compatible_nodes = [resource_to_node[resource]]
                break
                
        # Handle special case for gateway
        if deployment_name == "api-gateway":
            compatible_nodes = ["minikube"]
        
        # Create deployment based on our template
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": deployment_name},
            "spec": {
                "replicas": 1,
                "selector": {"matchLabels": {"app": deployment_name}},
                "template": {
                    "metadata": {
                        "labels": {
                            "app": deployment_name,
                            "monitoring": "true"
                        }
                    },
                    "spec": {
                        "nodeSelector": {
                            "kubernetes.io/hostname": compatible_nodes[0]
                        },
                        "containers": [
                            {
                                "name": deployment_name,
                                "image": image_name,
                                "imagePullPolicy": "Never",
                                "ports": comp_config["ports"]
                            }
                        ]
                    }
                }
            }
        }
        
        # Add serviceAccountName for api-gateway
        if deployment_name == "api-gateway":
            deployment["spec"]["template"]["spec"]["serviceAccountName"] = "flask-app-sa"
        
        deployments.append(deployment)
        
        # Create service
        service_ports = comp_config["service_ports"]
        
        service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": f"{deployment_name}-service"
            },
            "spec": {
                "selector": {"app": deployment_name},
                "ports": service_ports,
                "type": "NodePort"
            }
        }
        
        # Add labels for api-gateway service
        if deployment_name == "api-gateway":
            service["metadata"]["labels"] = {"app": deployment_name}
            
        services.append(service)
    
    return deployments, services


def generate_k8s_yaml(design_data, output_file):
    """Generate Kubernetes YAML from design time data"""
    
    # Define component mapping with detailed configuration
    component_map = {
        "c0": {
            "name": "api-gateway",
            "image": "flask-app-gateway:latest",
            "ports": [
                {"containerPort": 5000, "name": "http"},
                {"containerPort": 8000, "name": "metrics"}
            ],
            "service_ports": [
                {"name": "http", "port": 5000, "targetPort": 5000},
                {"name": "metrics", "port": 8000, "targetPort": 8000}
            ]
        },
        "c1": {
            "name": "flask-app-1",
            "image": "flask-app1:latest",
            "ports": [{"containerPort": 5000}],
            "service_ports": [{"port": 5000, "targetPort": 5000}]
        },
        "c2": {
            "name": "flask-app-2",
            "image": "flask-app2:latest",
            "ports": [{"containerPort": 5000}],
            "service_ports": [{"port": 5000, "targetPort": 5000}]
        }
    }
    
    # Create deployments and services
    deployments, services = create_deployments_from_components(design_data, component_map)
    
    # Assemble the final YAML documents
    k8s_docs = []
    
    # Interleave deployments and services
    for i in range(len(deployments)):
        k8s_docs.append(deployments[i])
        k8s_docs.append(services[i])
    
    # Write YAML with proper document separators
    with open(output_file, 'w') as file:
        for i, doc in enumerate(k8s_docs):
            if i > 0:
                file.write("---\n")
            yaml.dump(doc, file, default_flow_style=False)
            
    print(f"Generated Kubernetes manifest: {output_file}")


if __name__ == "__main__":
    # File paths
    design_file = "design_time_custom.json"
    output_file = "generated-flask-app.yaml"
    
    # Check if design file exists
    if not os.path.exists(design_file):
        print(f"Error: Design time file '{design_file}' not found")
        exit(1)
    
    # Load design time JSON
    design_data = load_design_time_json(design_file)
    
    # Generate Kubernetes YAML
    generate_k8s_yaml(design_data, output_file)
