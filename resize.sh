#!/bin/sh

num_nodes="${1:-3}"

if ! [ "$num_nodes" -lt "${minnodes:-3}" ]
then
    if [ "${clustername:-}" = "" ]
    then
        clustername="$(gcloud container clusters list | head -2 | tail -1 | sed -e 's/\s\s*/\n/g' | head -1)"
    fi
    if [ "${zonename:-}" = "" ]
    then
        zonename="$(gcloud container clusters list | head -2 | tail -1 | sed -e 's/\s\s*/\n/g' | head -2 | tail -1)"
    fi
    poolname="$(gcloud container clusters describe $clustername --region $zonename | grep name: | tail -1 | sed 's/.*: //g')"

    # echo for default option at Y/n prompt
    echo | gcloud container clusters resize $clustername --node-pool $poolname --region $zonename --num-nodes "$num_nodes"
else
    echo $num_nodes too small. Min ${minnodes:-3}
fi
