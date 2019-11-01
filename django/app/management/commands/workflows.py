import json
import time
import random
import string
from app.models import *
from app.images import *
from kubernetes import client, config, watch
import uuid as uu


def id_for(key, workflow_ids):
    key = str(key)
    workflow_ids[key] = workflow_ids.get(key, str(uu.uuid4()))
    return workflow_ids[key]


def prepare_workflow(workflow):
    body = workflow.json

    nodes = {}
    workflow_ids = {}

    for key, value in body['nodes'].items():
        i = id_for(key, workflow_ids)
        value['id'] = i
        value['old_id'] = key
        for _, v in value['inputs'].items():
            v = v['connections']
            for c in v:
                c['node'] = id_for(c['node'], workflow_ids)
        for _, v in value['outputs'].items():
            v = v['connections']
            for c in v:
                c['node'] = id_for(c['node'], workflow_ids)
        nodes[i] = value
    body['nodes'] = nodes
    workflow.json = body
    workflow.save()


def launch_workflow(workflow):
    body = workflow.json

    jobs = []
    for i, node in body['nodes'].items():
        j = Job(uuid=i, workflow=workflow, dependencies_met=False)
        j.json = node
        j.save()
        jobs.append(j)

        # temporary property
        j.has_no_dependencies = True

    for j in jobs:
        node = body['nodes'][j.pk]
        for _, inp in node['inputs'].items():
            for c in inp['connections']:
                dep = Job.objects.get(pk=c['node'])
                j.dependencies.add(dep)
                j.has_no_dependencies = False
        j.save()

    for j in filter(lambda j: j.has_no_dependencies, jobs):
        j.dependencies_met = True
        j.save()


def run_workflow(workflow):
    rnd = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))

    workflow.status = rnd
    workflow.scheduled = True
    workflow.save()

    # break race condition:
    time.sleep(0.1)
    workflow = Workflow.objects.get(pk=workflow.pk)
    if workflow.status != rnd:
        return

    prepare_workflow(workflow)
    launch_workflow(workflow)
    workflow.status = 'running'

    workflow.save()


def cron():
    while True:
        workflow = Workflow.objects.filter(
            should_run=True, scheduled=False).first()
        if workflow is None:
            break

        run_workflow(workflow)
