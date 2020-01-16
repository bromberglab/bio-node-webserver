import subprocess
import json
from ..docker import client
from docker.errors import ImageNotFound


def pull_if_needed(name, tag=None):
    if not ":" in name:
        tag = "latest" if tag is None else tag
        name += ":" + tag
    full_name = name
    tag = name.split(":")[1]
    name = name.split(":")[0]

    try:
        client.api.inspect_image(full_name)
    except ImageNotFound:
        img = client.images.pull(name, tag)


def get_image_meta(name, tag=None, delete=False):
    if not ":" in name:
        tag = "latest" if tag is None else tag
        name += ":" + tag

    pull_if_needed(name)
    info = client.api.inspect_image(name)

    labels = info["Config"].get("Labels", None)
    entrypoint = info["Config"].get("Entrypoint", None)
    cmd = info["Config"].get("Cmd", None)
    env = info["Config"].get("Env", None)
    labels = {} if labels is None else labels
    entrypoint = [] if entrypoint is None else entrypoint
    cmd = [] if cmd is None else cmd
    env = [] if env is None else env

    if delete:
        try:
            client.images.remove(name)
        except:
            pass  # wont force

    env_ = {}
    for e in env:
        k = e.split("=")[0]
        v = "=".join(e.split("=")[1:])
        env_[k] = v
    env = env_

    return labels, entrypoint, cmd, env


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


def cron_old():
    from ..models import Globals, NodeImage, NodeImageTag
    from .gcr import get_images, get_image_tags

    glob = Globals().instance
    if glob.gs_webhook_working and not glob.gs_webhook_fired:
        return
    glob.gs_webhook_fired = False
    glob.save()

    images = get_images()
    valid_images = []

    for i in images:
        labels, entrypoint, cmd, env = get_image_meta(i, delete=True)

        if not labels.get("default", False):
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

    for i in NodeImage.objects.exclude(name__in=valid_images).exclude(imported=True):
        i.delete()

    update_file_types()
