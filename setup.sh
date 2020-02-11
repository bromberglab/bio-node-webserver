#!/bin/sh

openssl aes-256-cbc -K "$encryption_key" -iv "$encryption_key"2 -in webservice-key.json.enc -out webservice-key.json -d
cat webservice-key.json | docker login -u _json_key --password-stdin https://gcr.io
gcloud auth activate-service-account --key-file webservice-key.json
gcloud container clusters get-credentials standard-cluster-1 --zone us-east4-a --project poised-cortex-254814
rm webservice-key.json.enc
unset encryption_key
kubectl get pods
mkdir /volume/logs
mkdir /volume/logs/django
mkdir /volume/logs/daemon
