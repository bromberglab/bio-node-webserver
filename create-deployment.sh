#!/bin/bash

gcloud container clusters get-credentials standard-cluster-1 --zone us-east4-a --project poised-cortex-254814

gcloud compute addresses create server-address --global

kubectl apply -f kube_configs/secret.yml

kubectl apply -f kube_configs/storage/classes.yml

helm reset --force || echo no helm installed.
kubectl delete -f kube_configs/storage/tiller.yml
kubectl apply -f kube_configs/storage/tiller.yml
helm init --history-max 200 --service-account tiller
echo "waiting for tiller to start ..."; sleep 15
helm install stable/nfs-server-provisioner -f kube_configs/storage/helm-config.yml
echo "waiting for nfs to start ..."; sleep 15
kubectl apply -f kube_configs/storage/pvc.yml
echo "waiting for pvc ..."; sleep 5

kubectl apply -f kube_configs/deployment.yml
echo "waiting for server to start ..."; sleep 30
kubectl apply -f kube_configs/ingress.yml
kubectl apply -f kube_configs/dist.yml
echo "waiting for dist copy ..."; sleep 15
kubectl delete -f kube_configs/dist.yml
echo "done. ingress may need ~5min to boot."

# [ -f gs_secret.txt ] || LC_ALL=C tr -dc "A-Za-z0-9-_" </dev/urandom | head -c 20 > gs_secret.txt
# echo "gs_secret: $(cat gs_secret.txt | tr -d '\n' | base64)"
# gsutil notification watchbucket -t "$(cat gs_secret.txt)" https://bio-no.de/webhooks/gs_update/ gs://artifacts.poised-cortex-254814.appspot.com
