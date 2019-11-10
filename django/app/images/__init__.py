import subprocess
import json


def get_images():
    p = subprocess.run(["gcloud", "container", "images", "list"], capture_output=True)
    r = p.stdout.decode()
    r = r.split("\n")[1:][:-1]
    # r = map(lambda i: i[len("gcr.io/poised-cortex-254814/"):], r)

    return r


def get_image_meta(name):
    subprocess.run(["./inspect.sh", name])
    with open("image_labels.json", "r") as f:
        labels = json.load(f)
    with open("image_entrypoint.json", "r") as f:
        entrypoint = json.load(f)
    with open("image_cmd.json", "r") as f:
        cmd = json.load(f)
    with open("image_env.json", "r") as f:
        env = json.load(f)

    return labels, entrypoint, cmd, env


def get_image_tags(name):
    p = subprocess.run(
        ["gcloud", "container", "images", "list-tags", name], capture_output=True
    )
    r = p.stdout.decode()
    r = r.split("\n")[1:]

    r = [(list(filter(None, t.split(" ")))[:-1] + [""])[:2] for t in r][:-1]

    return r


def add_file_type(set, type):
    for t in type.split("|"):
        if not "*" in t:
            set.add(t)


def update_file_types():
    from ..models import Upload, NodeImage, FileType

    file_types = set()

    us = Upload.objects.filter(is_finished=True)
    for u in us:
        file_types.add(u.file_type)

    images = NodeImage.objects.all()
    i: NodeImage
    for i in images:
        for t in i.inputs:
            add_file_type(file_types, t)
        for t in i.outputs:
            add_file_type(file_types, t)

    file_types = list(file_types)

    for i in FileType.objects.exclude(name__in=file_types):
        i.delete()
    for i in file_types:
        try:
            FileType.objects.get(name=i)
        except:
            FileType(name=i).save()


def cron():
    from ..models import Globals, NodeImage, NodeImageTag

    glob = Globals().instance
    if glob.gs_webhook_working and not glob.gs_webhook_fired:
        return
    glob.gs_webhook_fired = False
    glob.save()

    images = get_images()
    valid_images = []

    for i in images:
        labels, entrypoint, cmd, env = get_image_meta(i)

        if not labels.get("bio-node", False):
            continue
        valid_images.append(i)

        labels_string = json.dumps(labels).lower()
        entrypoint_string = json.dumps(entrypoint)
        cmd_string = json.dumps(cmd)
        env_string = json.dumps(env)
        tags = get_image_tags(i)
        tag_hashes = [t[0] for t in tags]

        try:
            image = NodeImage.objects.get(name=i)
            if (
                image.labels_string != labels_string
                or image.entrypoint_string != entrypoint_string
                or image.cmd_string != cmd_string
                or image.env_string != env_string
            ):
                image.labels_string = labels_string
                image.entrypoint_string = entrypoint_string
                image.cmd_string = cmd_string
                image.env_string = env_string
                image.save()
        except:
            image = NodeImage(
                name=i,
                labels_string=labels_string,
                entrypoint_string=entrypoint_string,
                cmd_string=cmd_string,
                env_string=env_string,
            )
            image.save()

        for tag_ in tags:
            h = tag_[0]
            n = tag_[1]
            try:
                tag = image.tag_refs.get(sha=h)
                if tag.name != n:
                    tag.name = n
                    tag.save()
            except:
                tag = NodeImageTag(image=image, sha=h, name=n)
                tag.save()

        for t in image.tag_refs.exclude(sha__in=tag_hashes):
            t.delete()

    for i in NodeImage.objects.exclude(name__in=valid_images):
        i.delete()

    update_file_types()
