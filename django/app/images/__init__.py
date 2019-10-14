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


def get_image_labels(name):
    subprocess.run(["./inspect.sh", name])
    with open("image_labels.json", 'r') as f:
        r = json.load(f)

    return r


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
