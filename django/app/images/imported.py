import json
from ..docker import client
from .base import get_image_meta, update_file_types


def import_image(name, tag=None, user=None):
    from ..models import NodeImage, NodeImageTag

    if not ":" in name:
        tag = "latest" if tag is None else tag
        name += ":" + tag
    full_name = name
    tag = name.split(":")[1]
    name = name.split(":")[0]

    img = client.images.pull(name, tag)
    labels, entrypoint, cmd, env = get_image_meta(name, tag, delete=True)

    id = img.attrs["RepoDigests"][0].split("@")[-1]
    if id.startswith("sha256:"):
        id = id[len("sha256:") :]

    image = NodeImage(
        name=name,
        labels_string=json.dumps(labels),
        entrypoint_string=json.dumps(entrypoint),
        cmd_string=json.dumps(cmd),
        env_string=json.dumps(env),
        imported=True,
        imported_tag=tag,
        imported_by=user if user.is_authenticated else None,
    )

    image.save()
    NodeImageTag(image=image, sha=id, name=tag).save()

    update_file_types()

    return image


def latest_hash(name, tag="latest"):
    r = client.api.inspect_distribution(name + ":" + tag)

    return r["Descriptor"]["digest"].split(":")[-1]


def update_image(name=None, user=None, image=None):
    from ..models import NodeImage, NodeImageTag

    if image is None:
        image = NodeImage.objects.get(name=name)
    else:
        name = image.name

    if user:
        assert (
            user.is_superuser or image.imported_by == user
        ), "Insufficient permissions."
    tag = image.imported_tag
    tag = tag if len(tag) else "latest"

    latest = latest_hash(name, tag)
    try:
        nodetag = image.tags.get(name=tag)
        if nodetag.sha == latest:
            return image
    except:
        pass

    img = client.images.pull(name, tag)
    labels, entrypoint, cmd, env = get_image_meta(name, tag, delete=True)

    id = img.attrs["RepoDigests"][0].split("@")[-1]
    if id.startswith("sha256:"):
        id = id[len("sha256:") :]

    image.labels_string = json.dumps(labels)
    image.entrypoint_string = json.dumps(entrypoint)
    image.cmd_string = json.dumps(cmd)
    image.env_string = json.dumps(env)

    image.save()

    try:
        nodetag = image.tags.get(name=tag)
        if nodetag.sha != id:
            nodetag.name = ""
            nodetag.save()
            NodeImageTag(image=image, sha=id, name=tag).save()
    except:
        NodeImageTag(image=image, sha=id, name=tag).save()

    update_file_types()

    return image


def cron():
    from ..models import NodeImage

    for image in NodeImage.objects.all():
        update_image(image=image)
