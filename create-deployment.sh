#!/bin/bash

gcloud compute addresses create server-address --global
kubectl apply -f deployment.yml

[ -f gs_secret.txt ] || LC_ALL=C tr -dc "A-Za-z0-9-_" </dev/urandom | head -c 20 > gs_secret.txt
echo "gs_secret: $(cat gs_secret.txt | tr -d '\n' | base64)"
gsutil notification watchbucket -t "$(cat gs_secret.txt)" https://bio-no.de/webhooks/gs_update/ gs://artifacts.poised-cortex-254814.appspot.com
