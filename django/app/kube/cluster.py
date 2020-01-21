import os
import time
import subprocess
from django.conf import settings


def resize(*a, **kw):
    import threading

    threading.Thread(target=resize_, args=a, kwargs=kw).start()


def resize_(num=None):
    """
    Resize cluster. num=None means minimum.
    """

    time.sleep(10)

    path = settings.BASE_DIR
    path = os.path.join(path, "resize.sh")
    cmd = [path]
    if num is not None:
        cmd += str(num)
    subprocess.run(cmd)
