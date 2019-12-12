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
    while logs is None:
        try:
            logs = api.read_namespaced_pod_log(name=pod, namespace="default")
        except:
            time.sleep(3)

    create_logfile(pod, logs)
    resp = k8s_batch_v1.delete_namespaced_job(job_name, namespace="default")
    api.delete_namespaced_pod(str(pod), namespace="default")

    job.handle_status(status, pod=pod)


def get_status_all():
    api = client.CoreV1Api()
    k8s_batch_v1 = client.BatchV1Api()

    w = watch.Watch()
    status = "running"
    pod = None
    while True:
        for event in w.stream(api.list_pod_for_all_namespaces, timeout_seconds=0):
            job = event["object"].metadata.labels.get("job-name", None)
            if job is not None:
                pod = event["object"].metadata.name
                status = event["object"].status.phase.lower()
                if status in ["succeeded", "failed"]:
                    handle_status(api, k8s_batch_v1, job, pod, status)


def launch_delete_job(body):
    api = client.CoreV1Api()
    k8s_batch_v1 = client.BatchV1Api()
    name = str(body["metadata"]["name"])
    resp = k8s_batch_v1.create_namespaced_job(body=body, namespace="default")
    status, pod = get_status(name, logging=False)
    resp = k8s_batch_v1.delete_namespaced_job(name, namespace="default")
    resp = api.delete_namespaced_pod(str(pod), namespace="default")


def _sum_containers(containers):
    totals_cpu = 0
    totals_memory = 0

    for container in containers:
        cpu = container["usage"]["cpu"]
        cpu = SIConverter.to_number(cpu)
        totals_cpu += 1000 * cpu
        memory = container["usage"]["memory"]
        memory = SIConverter.to_int(memory)
        totals_memory += memory / 1024 / 1024

    return totals_cpu, totals_memory


def get_resources(pod=None):
    """ returns cpu[m], memory[Mi] """

    import re
    from app.management.commands.resources import reg

    core = client.CoreV1Api()
    api = client.CustomObjectsApi()
    if pod is not None:
        response = api.get_namespaced_custom_object(
            "metrics.k8s.io", "v1beta1", "default", "pods", pod
        )

        return _sum_containers(response["containers"])
    else:
        pods = core.list_pod_for_all_namespaces(async_req=False)

        result = {}

        for pod in pods.items:
            try:
                name = pod.metadata.name
                if not re.match(reg, name):
                    continue
                resources = get_resources(name)
                result[name] = resources
            except:
                pass

        return result


class SIConverter:
    suffixes = {
        "Y": 24,
        "Z": 21,
        "E": 18,
        "P": 15,
        "T": 12,
        "G": 9,
        "M": 6,
        "k": 3,
        "h": 2,
        "da": 1,
        "": 0,
        "d": -1,
        "c": -2,
        "m": -3,
        "µ": -6.0,
        "u": -6,
        "n": -9,
        "p": -12,
        "f": -15,
        "a": -18,
        "z": -21,
        "y": -24,
    }

    i_suffixes = {
        "Ki": 1,
        "Mi": 2,
        "Gi": 3,
        "Ti": 4,
        "Pi": 5,
        "Ei": 6,
        "Zi": 7,
        "Yi": 8,
    }

    @classmethod
    def to_number(cls, str):
        last = str[-1]
        if last == " ":
            return cls.to_number(str[:-1])
        if last in string.digits:
            return float(str)
        if last == ".":
            return float(str)
        if last == "i":
            suffix = str[-2:]
            exponent = cls.i_suffixes[suffix]
            number = float(str[:-2])
            return number * (1024 ** exponent)
        exponent = cls.suffixes[last]
        number = float(str[:-1])
        return number * (10 ** exponent)

    @classmethod
    def to_int(cls, str):
        return int(cls.to_number(str))
