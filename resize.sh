#!/bin/sh

num_nodes="${1:-3}"

if [ "$num_nodes" -gt 2 ]
then
    cluster_name="$(gcloud container clusters list | head -2 | tail -1 | sed -e 's/\s\s*/\n/g' | head -1)"
    region_name="$(gcloud container clusters list | head -2 | tail -1 | sed -e 's/\s\s*/\n/g' | head -2 | tail -1)"
    pool_name="$(gcloud container clusters describe $cluster_name --region $region_name | grep name: | tail -1 | sed 's/.*: //g')"

    # echo for default option at Y/n prompt
    echo | gcloud container clusters resize $cluster_name --node-pool $pool_name --region $region_name --num-nodes "$num_nodes"
else
    echo $num_nodes too small.
fi