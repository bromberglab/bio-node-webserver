#!/bin/bash

gcloud config set project poised-cortex-254814
gcloud container clusters get-credentials standard-cluster-1 --zone us-east4-a --project poised-cortex-254814
