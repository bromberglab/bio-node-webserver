#!/bin/bash

docker pull "$1"
docker image inspect "$1" | jq '.[0]["Config"]["Labels"] // {}' > image_labels.json
docker image inspect "$1" | jq '.[0]["Config"]["Entrypoint"] // []' > image_entrypoint.json
docker image inspect "$1" | jq '.[0]["Config"]["Cmd"] // []' > image_cmd.json
docker image rm "$1"
