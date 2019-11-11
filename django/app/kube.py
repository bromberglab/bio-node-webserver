from kubernetes import client, watch


def get_status(name):
    api = client.CoreV1Api()
    # setup watch
    w = watch.Watch()
    status = "failed"
    pod = None
    for event in w.stream(api.list_pod_for_all_namespaces, timeout_seconds=0):
        if event["object"].metadata.labels.get("job-name", None) == str(name):
            pod = event["object"].metadata.name
            status = event["object"].status.phase.lower()
            if status in ["succeeded", "failed"]:
                break
    w.stop()

    logs = api.read_namespaced_pod_log(name=pod, namespace="default")

    return status, pod, logs


def launch_delete_job(body):
    api = client.CoreV1Api()
    k8s_batch_v1 = client.BatchV1Api()
    name = str(body["metadata"]["name"])
    resp = k8s_batch_v1.create_namespaced_job(body=body, namespace="default")
    status, pod, logs = get_status(name)
    resp = k8s_batch_v1.delete_namespaced_job(name, namespace="default")
    resp = api.delete_namespaced_pod(str(pod), namespace="default")
