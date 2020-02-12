import os
import time
import subprocess
from django.conf import settings
from kubernetes import client


def drain():
    """
    Drain cluster.
    """

    print("drain")
    api = client.CoreV1Api()
    safe_nodes = []
    unsafe_nodes = []
    for p in api.list_namespaced_pod(namespace="rook-ceph").items:
        name = p.metadata.name
        if "-osd-" in name and "-osd-prep" not in name:
            safe_nodes.append(p.spec.node_name)
    if len(safe_nodes) < settings.MIN_NODES:
        print("Too few nodes.")
        return False

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
    from app.models import Workflow, Globals

    if settings.DEBUG:
        return

    g = Globals().instance

    if Workflow.objects.filter(should_run=True, finished=False).count() == 0:
        if not g.drained:
            drain()
            g.drained = True
            g.save()
    else:
        if g.drained:
            g.drained = False
            g.save()

    if g.should_expand:
        g.should_expand = False
        g.save()
        if expand() == False:
            g.should_expand = True
            g.save()


def expand():
    api = client.CoreV1Api()

    print("expand")

    n = 0
    while n < 1:
        n = len(api.list_node().items)
    print(n)

    if n < settings.MAX_NODES:
        resize(n + 1)


def resize(num=None):
    """
    None for minimum size.
    """

    print("Resizing cluster to", num)
    num = settings.MIN_NODES if num is None else num

    if settings.MIN_NODES <= num <= settings.MAX_NODES:
        path = settings.BASE_DIR
        path = os.path.join(path, "resize.sh")
        cmd = [path]
        if num is not None:
            cmd += str(num)
        subprocess.run(cmd)
    else:
        print("Out of bounds")
