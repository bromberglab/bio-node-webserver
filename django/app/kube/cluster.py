import os
import time
import subprocess
from django.conf import settings
from kubernetes import client


def drain():
    """
    Drain cluster.
    """

    api = client.CoreV1Api()
    safe_nodes = []
    unsafe_nodes = []
    for p in api.list_namespaced_pod(namespace="rook-ceph").items:
        name = p.metadata.name
        if "-osd-" in name and "-osd-prep" not in name:
            safe_nodes.append(p.spec.node_name)
    for n in api.list_node().items:
        name = n.metadata.name
        if name not in safe_nodes:
            unsafe_nodes.append(name)
    pods = []
    for pod in api.list_pod_for_all_namespaces().items:
        if pod.spec.node_name in unsafe_nodes:
            pods.append((pod.metadata.name, pod.metadata.namespace))
    for name, namespace in pods:
        try:
            api.delete_namespaced_pod(name, namespace=namespace)
        except:
            pass
    for node in unsafe_nodes:
        print("delete node", node)
        api.delete_node(node)
    resize(len(safe_nodes))


def drain_if_no_workflows():
    from app.models import Workflow

    if settings.DEBUG:
        return

    if Workflow.objects.filter(should_run=True, finished=False).count() == 0:
        drain()


def resize(num=None):
    """
    None for minimum size.
    """

    path = settings.BASE_DIR
    path = os.path.join(path, "resize.sh")
    cmd = [path]
    if num is not None:
        cmd += str(num)
    subprocess.run(cmd)
