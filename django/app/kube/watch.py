from kubernetes import client, watch
import re
import time
import traceback
import threading
import urllib3.exceptions
from .jobs import create_logfile


DEBUG_WATCH = False


def retry(fun, times=2, wait=0.1, fail=False):
    error = None
    while times > 0:
        try:
            return fun()
        except Exception as e:
            error = e
            times -= 1
            if times > 0:
                time.sleep(wait)

    if fail:
        raise error


handled_pods = []


def handle_status(api, k8s_batch_v1, job_name, pod, status):
    global handled_pods
    from app.models import Job
    from app.management.commands.resources import reg

    if not re.match(reg, pod):
        if DEBUG_WATCH:
            print("no match")
        return

    if pod in handled_pods:
        return 1

    try:
        # job name is 'uuid-num', so we take the first 36 chars
        job = Job.objects.get(uuid=job_name[:36])
    except:
        if DEBUG_WATCH:
            print("no job")
        return

    logs = retry(lambda: api.read_namespaced_pod_log(name=pod, namespace="default"))
    logs = logs if isinstance(logs, str) else ""

    retry(
        lambda: k8s_batch_v1.delete_namespaced_job(job_name, namespace="default"),
        fail=True,
    )
    retry(
        lambda: api.delete_namespaced_pod(str(pod), namespace="default"),
        fail=False,
        wait=2,
        times=3,
    )

    if status != "succeeded" and job.retries_left > 0:
        if DEBUG_WATCH:
            print("retry")

        logs += "\nRetrying run ... (%d left)" % job.retries_left
        job.retry(job_name)
    else:
        if DEBUG_WATCH:
            print("handling")

        job.handle_status(status, pod=pod)
    create_logfile(pod, logs)

    handled_pods.append(pod)
    if len(handled_pods) > 1000:
        del handled_pods[0]

    return 1


def status_thread(api, k8s_batch_v1, lock, pods, tasks):
    while True:
        time.sleep(0.1)
        el = None
        with lock:
            if len(tasks) > 0:
                el = tasks[0]
                del tasks[0]

        if el is None:
            continue

        if DEBUG_WATCH:
            print("new task", el)

        try:
            r = handle_status(api, k8s_batch_v1, *el)
            if DEBUG_WATCH:
                print("handle_status", r)
            if r == 1:
                job = el[0]
                with lock:
                    if pods.get(job, None) is not None:
                        del pods[job]
        except Exception as e:
            if DEBUG_WATCH:
                print("Handling error:", e)
            # traceback.print_exc()


def pod_thread(lock, pods, api):
    w = watch.Watch()

    while True:
        for event in w.stream(
            api.list_namespaced_pod, namespace="default", timeout_seconds=120
        ):
            job = event["object"].metadata.labels.get("job-name", None)
            if job is not None:
                pod = event["object"].metadata.name
                with lock:
                    pods[job] = pod


def get_status_all():
    lock = threading.Lock()
    pods = {}
    tasks = []

    api = client.CoreV1Api()
    k8s_batch_v1 = client.BatchV1Api()
    threading.Thread(
        target=status_thread, args=(api, k8s_batch_v1, lock, pods, tasks)
    ).start()
    threading.Thread(target=pod_thread, args=(lock, pods, api)).start()

    w = watch.Watch()

    time.sleep(3)

    while True:
        try:
            for event in w.stream(
                k8s_batch_v1.list_namespaced_job,
                namespace="default",
                timeout_seconds=300,
            ):
                job = event["object"].metadata.name

                success = event["object"].status.succeeded is not None
                failure = event["object"].status.failed is not None

                status = "succeeded" if success else ("failed" if failure else None)

                if status is not None:
                    if DEBUG_WATCH:
                        print("new job", job, status)
                    with lock:
                        pod = pods.get(job, None)
                    if pod is None:
                        if DEBUG_WATCH:
                            print("no pod")
                        continue
                    with lock:
                        exists = False
                        for i, t in enumerate(tasks):
                            if t[0] == job:
                                old_pod = t[1]

                                t = list(t)
                                t[1] = pod
                                tasks[i] = tuple(t)
                                if DEBUG_WATCH:
                                    print(job, "already enlisted")
                                exists = True
                                break
                        if not exists:
                            tasks.append((job, pod, status))
                        elif pod != old_pod:
                            retry(
                                lambda: api.delete_namespaced_pod(
                                    str(old_pod), namespace="default"
                                ),
                                fail=False,
                                wait=2,
                                times=3,
                            )
        except urllib3.exceptions.MaxRetryError:
            pass
