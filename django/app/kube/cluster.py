import os
import time
import subprocess
from django.conf import settings
from kubernetes import client


def drain():
    from app.models import Globals

    """
    Drain cluster.
    """

    print("drain")
    api = client.CoreV1Api()
    safe_nodes = Globals().instance.nodes
    unsafe_nodes = []
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
        if not "server-deployment" in name:
            try:
                api.delete_namespaced_pod(name, namespace=namespace)
            except:
                pass
    for node in unsafe_nodes:
        api.delete_namespaced_config_map(
            "local-device-" + node, async_req=True, namespace="rook-ceph"
        )
    for node in unsafe_nodes:
        print("delete node", node)
        api.delete_node(node, async_req=True)
    resize(len(safe_nodes))


def drain_if_no_workflows():
    from app.models import Workflow, Globals

    if settings.DEBUG:
        return

    g = Globals().instance

    if Workflow.objects.filter(should_run=True, finished=False).count() == 0:
        if not g.drained:
            g.drained = True
            g.save()
            if drain() == False:
                g.drained = False
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
    from app.models import Globals

    safe_nodes = Globals().instance.nodes
    if len(safe_nodes) < settings.MIN_NODES:
        # Prevent cluster from expanding until we saved all the nodes of the minimum configuration.
        return False

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


def init_check():
    from app.models import Globals

    if settings.DEBUG:
        return

    api = client.CoreV1Api()
    n = 0
    while n < 1:
        nodes = api.list_node().items
        n = len(nodes)

    nodes = [n.metadata.name for n in nodes]

    if n == settings.MIN_NODES:
        resize(n)
        g = Globals().instance
        g.nodes = nodes
        g.save()
