#!/bin/bash

docker pull "$1"
docker image inspect "$1" | jq '.[0]["Config"]["Labels"] // {}' > image_labels.json
docker image rm "$1"
