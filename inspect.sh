#!/bin/bash

[ -f webservice-key.json ] || (openssl aes-256-cbc -K "$encryption_key" -iv "$encryption_key"2 -in webservice-key.json.enc -out webservice-key.json -d)
cat webservice-key.json | docker login -u _json_key --password-stdin https://gcr.io
docker pull "$1"
docker image inspect "$1" > image_info.json
docker image rm "$1"
