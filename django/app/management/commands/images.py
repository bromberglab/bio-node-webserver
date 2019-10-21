import json
from app.models import *
from app.images import *


def cron():
    glob = Globals().instance
    if glob.gs_webhook_working and not glob.gs_webhook_fired:
        return
    glob.gs_webhook_fired = False
    glob.save()

    images = get_images()
    valid_images = []

    for i in images:
        labels, cmd, env = get_image_meta(i)
        if labels.get("bionode_entrypoint", False):
            cmd = labels["bionode_entrypoint"].split(" ")

        if not labels.get('bio_node', False):
            continue
        valid_images.append(i)

        labels_string = json.dumps(labels).lower()
        cmd_string = json.dumps(cmd)
        env_string = json.dumps(env)
        tags = get_image_tags(i)
        tag_hashes = [t[0] for t in tags]

        try:
            image = NodeImage.objects.get(name=i)
            if image.labels_string != labels_string \
                    or image.cmd_string != cmd_string \
                    or image.env_string != env_string:
                image.labels_string = labels_string
                image.cmd_string = cmd_string
                image.env_string = env_string
                image.save()
        except:
            image = NodeImage(
                name=i, labels_string=labels_string,
                cmd_string=cmd_string, env_string=env_string
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
