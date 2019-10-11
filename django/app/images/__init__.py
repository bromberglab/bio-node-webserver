import subprocess


def list_images():
    p = subprocess.run([
        "gcloud", "container", "images", "list"
    ], capture_output=True)
    r = p.stdout.decode()
    return r.split("\n")[1:][:-1]
