from kubernetes import client, watch
import string


def get_status(name):
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

    return status, pod, logs


def launch_delete_job(body):
    api = client.CoreV1Api()
    k8s_batch_v1 = client.BatchV1Api()
    name = str(body["metadata"]["name"])
    resp = k8s_batch_v1.create_namespaced_job(body=body, namespace="default")
    status, pod, logs = get_status(name)
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

    api = client.CustomObjectsApi()
    if pod is not None:
        response = api.get_namespaced_custom_object(
            "metrics.k8s.io", "v1beta1", "default", "pods", pod
        )

        return _sum_containers(response["containers"])
    else:
        response = api.list_namespaced_custom_object(
            "metrics.k8s.io", "v1beta1", "default", "pods"
        )

        result = {}

        for item in response["items"]:
            name = item["metadata"]["name"]
            resources = _sum_containers(item["containers"])
            result[name] = resources

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
