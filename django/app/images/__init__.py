import subprocess
import json


def get_images():
    p = subprocess.run([
        "gcloud", "container", "images", "list"
    ], capture_output=True)
    r = p.stdout.decode()
    r = r.split("\n")[1:][:-1]
    # r = map(lambda i: i[len("gcr.io/poised-cortex-254814/"):], r)

    return r


def get_image_meta(name):
    subprocess.run(["./inspect.sh", name])
    with open("image_labels.json", 'r') as f:
        labels = json.load(f)
    with open("image_entrypoint.json", 'r') as f:
        entrypoint = json.load(f)
    with open("image_cmd.json", 'r') as f:
        cmd = json.load(f)
    with open("image_env.json", 'r') as f:
        env = json.load(f)

    return labels, entrypoint + cmd, env


def get_image_tags(name):
    p = subprocess.run([
        "gcloud", "container", "images", "list-tags", name
    ], capture_output=True)
    r = p.stdout.decode()
    r = r.split("\n")[1:]

    r = [
        (list(filter(None, t.split(' ')))[:-1] + [''])[:2]
        for t in r
    ][:-1]

    return r
