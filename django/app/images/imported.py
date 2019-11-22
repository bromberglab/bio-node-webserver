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

    id = img.short_id
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
        imported_by=user,
    )

    image.save()
    NodeImageTag(image=image, sha=id, name=tag).save()

    update_file_types()

    return image
