from kubernetes import client, watch
from django.conf import settings
from pathlib import Path
from app.util import now
import string
import os

from .jobs import create_logfile


def handle_status(api, k8s_batch_v1, job_name, pod, status):
    from app.models import Job
    from app.management.commands.resources import reg
    import re
    import time

    if not re.match(reg, pod):
        return

    try:
        # job name is 'uuid-num', so we take the first 36 chars
        job = Job.objects.get(uuid=job_name[:36])
    except:
        return

    logs = None
    tries = 5
    while logs is None:
        tries -= 1
        if tries < 0:
            logs = ""
        else:
            try:
                logs = api.read_namespaced_pod_log(name=pod, namespace="default")
            except:
                time.sleep(3)

    try:
        resp = k8s_batch_v1.delete_namespaced_job(job_name, namespace="default")
        job.handle_status(status, pod=pod)
        create_logfile(pod, logs)
        pass  # api.delete_namespaced_pod(str(pod), namespace="default")
    except:
        pass


def status_thread(lock, list):
    import time
    import traceback

    while True:
        time.sleep(0.1)
        el = None
        try:
            with lock:
                el = list[0]
                del list[0]
        except:
            pass

        if el is None:
            continue

        try:
            handle_status(*el)
        except Exception as e:
            print("Handling error:", e)
            traceback.print_exc()


def get_status_all():
    import threading

    lock = threading.Lock()
    tasks = []
    threading.Thread(target=status_thread, args=(lock, tasks)).start()

    api = client.CoreV1Api()
    k8s_batch_v1 = client.BatchV1Api()

    w = watch.Watch()
    status = "running"
    pod = None
    while True:
        for event in w.stream(
            api.list_namespaced_pod, namespace="default", timeout_seconds=120
        ):
            job = event["object"].metadata.labels.get("job-name", None)
            if job is not None:
                pod = event["object"].metadata.name
                status = event["object"].status.phase.lower()
                if status in ["succeeded", "failed"]:
                    with lock:
                        tasks.append((api, k8s_batch_v1, job, pod, status))

