#!/bin/sh

cat /keys/sa-key.json | docker login -u _json_key --password-stdin https://gcr.io
gcloud auth activate-service-account --key-file /keys/sa-key.json
gcloud container clusters get-credentials $clustername --zone $zonename --project $projectname
kubectl get pods>/dev/null
mkdir /volume/logs
mkdir /volume/logs/django
mkdir /volume/logs/daemon
rm /volume/logs/daemon/watch.log
export GOOGLE_APPLICATION_CREDENTIALS="/keys/sa-key.json"
