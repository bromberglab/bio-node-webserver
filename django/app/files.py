import threading
from pathlib import Path
from django.conf import settings
import os
import shutil
import random
import string
from app.models import *

base_path = Path(settings.DATA_PATH)
base_path /= 'data'

rnd = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))


def _handle_uploaded_file(request):
    threading.Thread(target=lambda: _handle_uploaded_file(request)).start()


def handle_uploaded_file(request):
    data = request.data
    upload = get_upload(request)

    file = data['file']
    chunkNumber = data['chunkNumber']
    totalChunks = int(data['totalChunks'])
    uuid = str(upload.uuid)
    relativePath = data['relativePath']
    filename = data['filename']
    file_type = data.get('type', 'file')

    relativePath = Path(relativePath)
    # TODO make better ...
    relativePath = relativePath.parent / (rnd + "_" + relativePath.name)

    save_file(file, base_path / file_type / uuid /
              relativePath / chunkNumber, totalChunks, filename)


def save_file(file, path: Path, totalChunks=0, filename="file"):
    suffix = '.partial_chunk'

    path = path.with_suffix(suffix)
    os.makedirs(path.parent, exist_ok=True)
    with open(path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    num_files = len([f for f in os.listdir(path.parent)])
    if num_files == totalChunks:
        with open(path.parent.parent / filename, 'wb+') as wfd:
            for i in range(totalChunks):
                partial_path = path.parent / str(i+1)
                partial_path = partial_path.with_suffix(suffix)

                with open(partial_path, 'rb+') as fd:
                    shutil.copyfileobj(fd, wfd)
                os.remove(partial_path)
            os.rmdir(path.parent)


def get_upload(request):
    pk = request.session.get('upload_pk', None)
    upload = None
    if pk is not None:
        upload = Upload.objects.get(pk=pk)
    if upload is None or upload.is_finished:
        upload = Upload()
        if request.user.is_authenticated:
            upload.user = request.user
        upload.save()
        pk = upload.pk
        request.session['upload_pk'] = str(pk)

    return upload
