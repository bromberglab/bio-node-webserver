import threading
from pathlib import Path
from django.conf import settings
import os
import shutil
import random
import string

base_path = Path(settings.DATA_PATH)
base_path /= 'data'

rnd = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))


def _handle_uploaded_file(data):
    threading.Thread(target=lambda: _handle_uploaded_file(data)).start()


def handle_uploaded_file(data):
    # TODO: Enforce closing of uploads, so that existing uploads cannot be overridden by anyone.

    file = data['file']
    chunkNumber = data['chunkNumber']
    totalChunks = int(data['totalChunks'])
    uuid = data['identifier']
    relativePath = data['relativePath']
    filename = data['filename']
    file_type = data.get('type', 'file')

    relativePath = Path(relativePath)
    # TODO make better ...
    relativePath = relativePath.parent / (rnd + "_" + relativePath.name)

    save_file(file, base_path / file_type / uuid /
              relativePath / chunkNumber, totalChunks, filename)


def save_file(file, path: Path, totalChunks=0, filename="file"):
    os.makedirs(path.parent, exist_ok=True)
    with open(path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    num_files = len([f for f in os.listdir(path.parent)])
    if num_files == totalChunks:
        with open(path.parent.parent / filename, 'wb+') as wfd:
            for i in range(totalChunks):
                with open(path.parent / str(i+1), 'rb+') as fd:
                    shutil.copyfileobj(fd, wfd)
                os.remove(path.parent / str(i + 1))
            os.rmdir(path.parent)
