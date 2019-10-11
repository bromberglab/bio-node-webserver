import subprocess
import json


def list_images():
    p = subprocess.run([
        "gcloud", "container", "images", "list"
    ], capture_output=True)
    r = p.stdout.decode()
    r = r.split("\n")[1:][:-1]
    r = map(lambda i: i[len("gcr.io/poised-cortex-254814/"):], r)

    return list(r)


def inspect_image(name):
    subprocess.run(["./inspect.sh", 'gcr.io/poised-cortex-254814/' + name])
    with open("image_labels.json", 'r') as f:
        r = json.load(f)

    return r
