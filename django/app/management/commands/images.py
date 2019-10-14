import json
from app.models import *
from app.images import *


def cron():
    images = get_images()
    valid_images = []

    for i in images:
        labels = get_image_labels(i)

        if not labels.get('bio_node', False):
            continue
        valid_images.append(i)

        labels_string = json.dumps(labels)
        tags = get_image_tags(i)
        tag_hashes = [t[0] for t in tags]

        try:
            image = NodeImage.objects.get(name=i)
            if image.labels_string != labels_string:
                image.labels_string = labels_string
                image.save()
        except:
            image = NodeImage(name=i, labels_string=labels_string)
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
