#!/bin/sh

cat /keys/sa-key.json | docker login -u _json_key --password-stdin https://gcr.io
gcloud auth activate-service-account --key-file /keys/sa-key.json
gcloud container clusters get-credentials $clustername --zone $zonename --project $projectname
kubectl get pods>/dev/null
mkdir /volume/logs
mkdir /volume/logs/django
mkdir /volume/logs/daemon
rm /volume/logs/daemon/watch.log
export GOOGLE_APPLICATION_CREDENTIALS="/keys/sa-key.json"

cron_reboot() {
    HOUR=3 # TZ=EST
    secondsleft=$(python3 -c 'import datetime; print(24*60*60 - int((datetime.datetime.now() - datetime.datetime.now().replace(hour='$HOUR', minute=0, second=0)).total_seconds()))')
    sleep ${secondsleft}s
    sleep 1d
    reboot
}

# cron_reboot &
