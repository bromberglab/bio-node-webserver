#!/bin/bash

docker pull "$1"
docker image inspect "$1" > image_meta.json
cat image_meta.json | jq '.[0]["Config"]["Labels"] // {}' > image_labels.json
cat image_meta.json | jq '.[0]["Config"]["Entrypoint"] // []' > image_entrypoint.json
cat image_meta.json | jq '.[0]["Config"]["Cmd"] // []' > image_cmd.json
cat image_meta.json | jq '.[0]["Config"]["Env"] // []' > image_env.json
docker image rm "$1"
