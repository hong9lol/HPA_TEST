#!/bin/sh

minikube delete
minikube start --nodes=2 --cpus=max --kubernetes-version=v1.27.0-rc.0 --feature-gates=InPlacePodVerticalScaling=true

kubectl apply -f k8s/manifests/simple_app.yaml
kubectl expose deployment simple-app-deployment --type=LoadBalancer --port=8080 & 

minikube service simple-app-deployment
minikube service list -n default -o json | jq '.[1].URLs[0]' > target_url.txt
minikube addons enable metrics-server