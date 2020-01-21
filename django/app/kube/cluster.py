import os
import subprocess
from django.conf import settings


def resize(num=None):
    """
    Resize cluster. num=None means minimum.
    """

    path = settings.BASE_DIR
    path = os.path.join(path, "resize.sh")
    cmd = [path]
    if num is not None:
        cmd += str(num)
    subprocess.run(cmd)
