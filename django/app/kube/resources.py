from kubernetes import client, watch
from django.conf import settings
from pathlib import Path
from app.util import now
import string
import os


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

    api = client.CustomObjectsApi()
    if pod is not None:
        response = api.get_namespaced_custom_object(
            "metrics.k8s.io", "v1beta1", "bio-node", "pods", pod
        )

        return _sum_containers(response["containers"])
    else:
        response = api.list_cluster_custom_object("metrics.k8s.io", "v1beta1", "pods")

        result = {}

        for item in response["items"]:
            name = item["metadata"]["name"]
            if not re.match(reg, name):
                continue
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
