import json
import time
import random
import string
from app.models import *
from app.images import *
from kubernetes import client, config, watch
from django.db import transaction
from app.files import copy_folder


def get_status(pk):
    api = client.CoreV1Api()

    # setup watch
    w = watch.Watch()
    status = "failed"
    pod = None
    for event in w.stream(api.list_pod_for_all_namespaces, timeout_seconds=0):
        if event["object"].metadata.labels.get("job-name", None) == str(pk):
            pod = event["object"].metadata.name
            if event["type"] == "MODIFIED":
                status = event["object"].status.phase.lower()
                if status in ["succeeded", "failed"]:
                    break
    w.stop()

    return status, pod


def create_output(job):
    conf = job.json
    data_output_type = job.data_output_type
    data_id = str(job.data_id)
    out_path = "data/" + data_output_type + "/" + data_id

    if len(conf["inputs"].items()) != 1:
        return  # misconfigured, ignore.

    # TODO: Refactor duplicate code
    for i, inp in enumerate(conf["inputs"].items()):
        inp = inp[1]  # ignore key, take value
        if len(inp["connections"]) == 0:
            return  # misconfigured, ignore.
        connection = inp["connections"][0]  # TODO: multiple?

        inp_id = connection["node"]  # TODO: multiple
        inp_job = Job.objects.get(pk=inp_id)
        inp_path = "data/job_outputs/" + inp_id
        if inp_job.is_data_input:
            inp_path = "data/" + inp_job.data_input_type + "/" + str(inp_job.data_id)
        elif not inp_job.is_single_output:
            inp_path += "/" + connection.output[2:]

    copy_folder(inp_path, out_path)


def launch_job(job):
    dep = json.loads(job.body)

    dep["metadata"]["name"] = str(job.pk)
    k8s_batch_v1 = client.BatchV1Api()
    resp = k8s_batch_v1.create_namespaced_job(body=dep, namespace="default")


def delete_job(name, pod):
    k8s_batch_v1 = client.BatchV1Api()
    k8s_v1 = client.CoreV1Api()
    resp = k8s_batch_v1.delete_namespaced_job(str(name), namespace="default")
    resp = k8s_v1.delete_namespaced_pod(str(pod), namespace="default")


def run_job(job):
    rnd = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))

    job.status = rnd
    job.scheduled = True
    job.save()

    # break race condition:
    time.sleep(0.1)
    job = Job.objects.get(pk=job.pk)
    if job.status != rnd:
        return

    job.status_change()
    status = ""
    if job.is_node:
        # configure client
        config.load_kube_config()

        job.create_body()
        launch_job(job)
        status, pod = get_status(job.pk)

        delete_job(job.pk, pod)
    elif job.is_data_output:
        create_output(job)

    job.status = status

    with transaction.atomic():
        job.finish()

        w = job.workflow
        if w and w.job_set.filter(finished=False).count() == 0:
            w.finish()

    job = Job.objects.get(pk=job.pk)
    for dependent in job.dependents.all():
        with transaction.atomic():
            dependent.dependencies.remove(job)
            if dependent.dependencies.count() == 0:
                dependent.dependencies_met = True
            dependent.save()


def cron():
    glob = Globals().instance

    while True:
        job = Job.objects.filter(scheduled=False, dependencies_met=True).first()
        if job is None:
            break

        run_job(job)
