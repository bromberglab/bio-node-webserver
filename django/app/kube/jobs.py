from kubernetes import client, watch
from django.conf import settings
from pathlib import Path
from app.util import now
import string
import os


def create_logfile(pod, logs):
    if pod is None:
        return

    t = now()

    file = t.strftime("%Y-%m-%d %H:%M:%S.log")

    path = Path(settings.DATA_PATH) / "logs" / "/".join(pod.split("-")) / file
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "w") as f:
        f.write(logs)


def get_status(name, logging=True):
    api = client.CoreV1Api()
    # setup watch
    w = watch.Watch()
    status = "running"
    pod = None
    while status not in ["succeeded", "failed"]:
        for event in w.stream(api.list_pod_for_all_namespaces, timeout_seconds=0):
            if event["object"].metadata.labels.get("job-name", None) == str(name):
                pod = event["object"].metadata.name
                status = event["object"].status.phase.lower()
                if status in ["succeeded", "failed"]:
                    break
    w.stop()

    logs = api.read_namespaced_pod_log(name=pod, namespace="default")
    if logging:
        create_logfile(pod, logs)

    return status, pod


def launch_delete_job(body):
    api = client.CoreV1Api()
    k8s_batch_v1 = client.BatchV1Api()
    name = str(body["metadata"]["name"])
    resp = k8s_batch_v1.create_namespaced_job(body=body, namespace="default")
    status, pod = get_status(name, logging=False)
    resp = k8s_batch_v1.delete_namespaced_job(name, namespace="default")
    resp = api.delete_namespaced_pod(str(pod), namespace="default")
