#!/bin/sh

echo ====== Start ======
echo 1. Delete Old Cluster and Create New Cluster
# delete cluster
gcloud container clusters delete cluster-1 --region us-central1-a
gcloud config set project kubernetes-hpa
# create cluster
gcloud container clusters create cluster-1 --enable-cloud-run-alpha --enable-kubernetes-alpha --no-enable-autorepair --no-enable-autoupgrade --cluster-version 1.27.6 --region us-central1-a
sleep 180

#echo 1. Remove Application and Service
#kubectl delete pod --all
#kubectl delete deployments.apps simple-app-deployment
#kubectl delete service simple-app-deployment

echo 2. Start Test Application and Service
kubectl apply -f k8s/manifests/simple_app.yaml
sleep 60
kubectl expose deployment simple-app-deployment --type=LoadBalancer --port=8080 & 
sleep 120
kubectl get service -o wide --no-headers | grep simple-app-deployment |  awk '/[[:space:]]/ {print "http://" $4 ":8080"}' > target_url.txt

echo 3. Start Metrics-server
containerName=`kubectl get pod -n kube-system | grep metrics-server | awk '/[[:space:]]/ {print $1}'`
deploymentName=`echo $containerName | awk  '{split($1,a,"-"); print a[1]"-"a[2]"-"a[3]}'`
image=`kubectl get deployments.apps -n kube-system $deploymentName -o wide --no-headers | awk '/[[:space:]]/ {print $7}' | awk  '{split($1,a,","); print a[1]}'`
image=''''\"${image}\"''''

echo "[Image]"
echo $image 
echo "[deploymentName, containerName]"
echo $deploymentName $containerName

# kubectl patch -n kube-system deployments.apps "$deploymentName" -p '''{"spec":{"template":{"spec":{"containers":[{"name":"metrics-server", "image": '${image}', "command":["--cert-dir=/tmp","--secure-port=10250","--kubelet-preferred-address-types=InternalIP,Hostname,InternalDNS,ExternalDNS,ExternalIP", "--metric-resolution=15s"]}]}}}}'''
kubectl patch -n kube-system deployments "$deploymentName" -p '''{"spec":{"template":{"spec":{"containers":[{"name":"metrics-server", "image": '${image}', "command":["--metric-resolution=15s"]}]}}}}'''

sleep 10
kubectl rollout restart -n kube-system deployments "$deploymentName"
sleep 60
kubectl get deployments.apps -n kube-system "$deploymentName" --template='{{range $k := .spec.template.spec.containers}}{{$k.command}}{{"\n"}}{{end}}' | grep -o 'metric-resolution=[^] ]*'

echo ====== Done ======