#!/bin/bash

gcloud compute addresses create server-address --global
kubectl apply -f deployment.yml
