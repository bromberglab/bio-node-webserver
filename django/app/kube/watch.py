from kubernetes import client, watch
import re
import time
import traceback
import threading
import urllib3.exceptions
from .jobs import create_logfile
from django.utils.timezone import now
from django.conf import settings
import json
from app.util import now, dtformat


DEBUG_WATCH = True


def debug_print(*msg, high_frequency=False):
    if not DEBUG_WATCH:
        return

    msg = str(msg)
    fullmsg = "[%s] %s" % (now().strftime(dtformat), msg)

    logdir = settings.BASE_DIR + "/watch.log"
    hflogdir = settings.BASE_DIR + "/watch.log.latest"

    if settings.DEBUG:
        print(fullmsg)

    if not high_frequency:
        with open(logdir, "a") as f:
            f.write(str(fullmsg) + "\n")
    else:
        try:
            with open(hflogdir, "r") as f:
                logs = f.read()
            logs = json.loads(logs)
        except:
            logs = {}
        logs[msg] = fullmsg
        with open(hflogdir, "w") as f:
            json.dump(logs, f)


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


def handle_status(
    api, k8s_batch_v1, unhandled_pods, unhandled_jobs, job_name, pod, status
):
    global handled_pods
    from app.models import Job
    from app.management.commands.resources import reg

    if not re.match(reg, pod):
        debug_print("no match")
        return

    if pod in handled_pods:
        return 1

    try:
        # job name is 'uuid-num', so we take the first 36 chars
        # remove bio prefix
        job = Job.objects.get(uuid=job_name[3:39])
    except:
        debug_print("no job")
        retry(
            lambda: k8s_batch_v1.delete_namespaced_job(job_name, namespace="default"),
            fail=False,
        )
        return

    if unhandled_jobs.get(job_name, None) is not None:
        del unhandled_jobs[job_name]
    if unhandled_pods.get(pod, None) is not None:
        del unhandled_pods[pod]

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
        debug_print("retry")

        logs += "\nRetrying run ... (%d left)" % job.retries_left
        job.retry(job_name)
    else:
        debug_print("handling")

        job.handle_status(status, pod=pod)
    create_logfile(pod, logs)

    handled_pods.append(pod)
    if len(handled_pods) > 1000:
        del handled_pods[0]

    return 1


def status_thread(api, k8s_batch_v1, lock, pods, tasks, unhandled_pods, unhandled_jobs):
    unhandled_check = now()

    while True:
        debug_print("loop status_thread", high_frequency=True)
        time.sleep(0.1)
        el = None
        with lock:
            if len(tasks) > 0:
                el = tasks[0]
                del tasks[0]

        if el is None:
            continue

        debug_print("new task", el)

        try:
            r = handle_status(api, k8s_batch_v1, unhandled_pods, unhandled_jobs, *el)
            debug_print("handle_status", r)
            if r == 1:
                job = el[0]
                with lock:
                    if pods.get(job, None) is not None:
                        del pods[job]
        except Exception as e:
            debug_print("Handling error:", e)
            # traceback.print_exc()

        if (now() - unhandled_check).total_seconds() > 5 * 60:  # 5min
            """
            Remove ghost jobs and pods.
            """
            unhandled_check = now()
            del_items = []
            for pod, t in unhandled_pods.items():
                if (now() - t).total_seconds() > 60 * 60:  # 60min
                    job = "-".join(pod.split("-")[:-1])

                    result = retry(
                        lambda: k8s_batch_v1.read_namespaced_job_status(
                            job, namespace="default"
                        ),
                        wait=2,
                        times=3,
                    )
                    if result is None:
                        retry(
                            lambda: api.delete_namespaced_pod(pod, namespace="default"),
                            fail=False,
                            wait=2,
                            times=3,
                        )
                        del_items.append(pod)
            for pod in del_items:
                del unhandled_pods[pod]

            del_items = []
            for job, t in unhandled_jobs.items():
                if (now() - t).total_seconds() > 60 * 60:  # 60min
                    result = pods.get(job, None)
                    if result is None:
                        retry(
                            lambda: k8s_batch_v1.delete_namespaced_job(
                                job, namespace="default"
                            ),
                            fail=False,
                            wait=2,
                            times=3,
                        )
                        del_items.append(job)
            for job in del_items:
                del unhandled_jobs[job]


def pod_thread(lock, pods, api, unhandled_pods, unhandled_jobs):
    from app.management.commands.resources import reg

    w = watch.Watch()

    while True:
        debug_print("loop pod_thread", high_frequency=True)
        for event in w.stream(
            api.list_namespaced_pod, namespace="default", timeout_seconds=120
        ):
            job = event["object"].metadata.labels.get("job-name", None)
            if job is not None:
                pod = event["object"].metadata.name
                if not re.match(reg, pod):
                    continue

                with lock:
                    pods[job] = pod

                if unhandled_pods.get(pod, None) is None:
                    unhandled_pods[pod] = now()


def get_status_all():
    global handled_pods
    lock = threading.Lock()
    pods = {}
    tasks = []
    unhandled_pods = {}
    unhandled_jobs = {}

    api = client.CoreV1Api()
    k8s_batch_v1 = client.BatchV1Api()
    threading.Thread(
        target=status_thread,
        args=(api, k8s_batch_v1, lock, pods, tasks, unhandled_pods, unhandled_jobs),
    ).start()
    threading.Thread(
        target=pod_thread, args=(lock, pods, api, unhandled_pods, unhandled_jobs)
    ).start()

    w = watch.Watch()

    time.sleep(3)

    while True:
        debug_print("loop get_status_all", high_frequency=True)
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
                    debug_print("new job", job, status)
                    with lock:
                        pod = pods.get(job, None)
                    if pod is None:
                        debug_print("no pod")
                        if unhandled_jobs.get(job, None) is None:
                            unhandled_jobs[job] = now()
                        continue
                    with lock:
                        exists = False
                        for i, t in enumerate(tasks):
                            if t[0] == job:
                                old_pod = t[1]

                                t = list(t)
                                t[1] = pod
                                tasks[i] = tuple(t)
                                debug_print(job, "already enlisted")
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
