from kubernetes import client, watch
import re
import time
import traceback
import threading
from .jobs import create_logfile


def handle_status(api, k8s_batch_v1, job_name, pod, status):
    from app.models import Job
    from app.management.commands.resources import reg

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

    resp = k8s_batch_v1.delete_namespaced_job(job_name, namespace="default")
    try:
        api.delete_namespaced_pod(str(pod), namespace="default")
    except:
        pass
    job.handle_status(status, pod=pod)
    create_logfile(pod, logs)


def status_thread(lock, list):
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


def pod_thread(pods, api):
    w = watch.Watch()

    while True:
        for event in w.stream(
            api.list_namespaced_pod, namespace="default", timeout_seconds=120
        ):
            job = event["object"].metadata.labels.get("job-name", None)
            if job is not None:
                pod = event["object"].metadata.name
                pods[job] = pod


def get_status_all():
    lock = threading.Lock()
    pods = {}
    tasks = []
    threading.Thread(target=status_thread, args=(lock, tasks)).start()

    api = client.CoreV1Api()
    threading.Thread(target=pod_thread, args=(pods, api)).start()
    k8s_batch_v1 = client.BatchV1Api()

    w = watch.Watch()

    while True:
        for event in w.stream(
            k8s_batch_v1.list_namespaced_job, namespace="default", timeout_seconds=120
        ):
            job = event["object"].metadata.name

            success = event["object"].status.succeeded is not None
            failure = event["object"].status.failed is not None

            status = "succeeded" if success else ("failed" if failure else None)

            if status is not None:
                try:
                    pod = pods[job]
                    del pods[job]
                except:
                    continue
                with lock:
                    tasks.append((api, k8s_batch_v1, job, pod, status))

