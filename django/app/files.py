import threading
from pathlib import Path
from django.conf import settings
import os
import re
import shutil
from shutil import move as stupid_broken_move
import random
import string
from app.models import *
from .images import update_file_types
import subprocess

base_path = Path(settings.DATA_PATH)
base_path /= "data"
chunk_suffix = ".partial_chunk"
chunk_suffix_done = chunk_suffix + "_done"

rnd = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))

# valid delimiters to separate job-name from file-name.
# i.e. job1-file.txt, job1_file.txt, etc.
delimiters = "([,_.\s-])"


def fixed_move_that_fixes_the_super_stupid_annoying_bug_that_pathlib_has(
    src, *args, **kwargs
):
    src = str(src)
    if src[-1] == "/":
        src = src[:-1]
    return stupid_broken_move(src, *args, **kwargs)


# shorter alias
move = fixed_move_that_fixes_the_super_stupid_annoying_bug_that_pathlib_has


def _handle_uploaded_file(request):
    threading.Thread(target=lambda: _handle_uploaded_file(request)).start()


def handle_uploaded_file(request):
    data = request.data
    upload = get_upload(request)

    file = data["file"]
    chunkNumber = data["chunkNumber"]
    totalChunks = int(data["totalChunks"])
    uuid = str(upload.uuid)
    relativePath = data["relativePath"]
    filename = data["filename"]
    file_type = "file"

    relativePath = Path(relativePath)
    # TODO make better ...
    relativePath = relativePath.parent / (rnd + "_" + relativePath.name)

    save_file(
        file,
        base_path / file_type / uuid / relativePath / chunkNumber,
        totalChunks,
        filename,
    )


def list_all_files(path, type=None, id=None, relative=True, only_full_uploads=True):
    if path is None:
        path = base_path
        path /= type
        path /= str(id)

    files = [os.path.join(dp, f) for dp, dn, fn in os.walk(path) for f in fn]
    files = [Path(f) for f in files]
    if only_full_uploads:
        files = [
            f
            for f in files
            if not (f.match("*" + chunk_suffix) or f.match("*" + chunk_suffix_done))
        ]

    if relative:
        files = [os.path.relpath(f, path) for f in files]
        files = [Path(f) for f in files]

    return files


def matches_any_suffix(f, suffixes):
    for s in suffixes:
        if f.match("*" + s):
            return True

    return False


def list_cleanup_files(type, id, relative=True):
    files = list_all_files(None, type, id, relative=relative, only_full_uploads=False)

    suffixes = [
        chunk_suffix,
        chunk_suffix_done,
        ".DS_Store",
    ]
    files = [f for f in files if matches_any_suffix(f, suffixes)]

    return files


def to_file_tree(files):
    tree = []

    for f in files:
        t = tree
        for p in f.parts[:-1]:
            t_ = [i for i in t if i["name"] == p]
            if len(t_):
                t_ = t_[0]
            else:
                t_ = {"name": p, "children": []}
                t.append(t_)
            t = t_["children"]
        t.append({"name": f.parts[-1]})

    return tree


def file_tree(type, id):
    files = list_all_files(None, type, id)

    return to_file_tree(files)


def save_file(file, path: Path, totalChunks=0, filename="file"):
    path = path.with_suffix(chunk_suffix)
    done_path = path.with_suffix(chunk_suffix_done)
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "wb+") as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    done_path.touch()

    num_files = len([f for f in os.listdir(path.parent)])
    if num_files == totalChunks * 2:
        with open(path.parent.parent / filename, "wb+") as wfd:
            for i in range(totalChunks):
                partial_path = path.parent / str(i + 1)
                partial_path = partial_path.with_suffix(chunk_suffix)
                partial_path_done = partial_path.with_suffix(chunk_suffix_done)

                with open(partial_path, "rb+") as fd:
                    shutil.copyfileobj(fd, wfd)
                os.remove(partial_path)
                os.remove(partial_path_done)
            os.rmdir(path.parent)


def get_upload(request):
    pk = request.session.get("upload_pk", None)
    upload = None
    if pk is not None:
        try:
            upload = Upload.objects.get(pk=pk)
        except:
            pass  # upload is still None
    if upload is None or upload.is_finished:
        upload = Upload()
        if request.user.is_authenticated:
            upload.user = request.user
        upload.save()
        pk = upload.pk
        request.session["upload_pk"] = str(pk)

    return upload


def file_extension(p: Path):
    name = p.name
    if name.startswith(".") and not "." in name[1:]:
        return name
    if name.endswith(".tar.gz"):
        return ".tar.gz"

    return p.suffix


def list_dirs(path):
    path = Path(path)
    files = os.listdir(path)
    files = [f for f in files if os.path.isdir(path / f)]

    return files


def list_files(path):
    path = Path(path)
    files = os.listdir(path)
    files = [f for f in files if os.path.isfile(path / f)]

    return files


def get_structure(path):
    files = [os.path.join(dp, f) for dp, dn, fn in os.walk(path) for f in fn]
    files = [os.path.relpath(f, path) for f in files]
    files = [Path(f) for f in files]
    files = [os.path.join(str(f.parent), file_extension(f)) for f in files]

    return files


def is_single_dir(path):
    path = Path(path)


def old_finalize_upload(request, upload):
    for u in Upload.objects.filter(
        name=upload.name, is_newest=True, file_type=upload.file_type
    ).exclude(pk=upload.pk):
        u.is_newest = False
        u.save()

    path = base_path
    path /= "file"
    path /= str(upload.uuid)
    to_path = base_path
    to_path /= upload.file_type
    to_path /= str(upload.uuid)

    for f in list_cleanup_files("file", str(upload.uuid), relative=False):
        os.remove(f)

    if path != to_path:
        os.makedirs(to_path.parent, exist_ok=True)
        move(path, to_path)

    update_file_types()


def filter_start(items, prefix):
    items = filter(lambda i: i.startswith(prefix), items)

    return list(items)


def find_prefix(splits, files):
    n = len(files)
    files.sort()
    prev_prefix = prefix = "".join(splits[:1])
    splits = splits[1:]

    while (
        len(filter_start(files, prev_prefix)) == n
        or len(filter_start(files, prefix)) > 1
    ) and len(splits):
        prev_prefix = prefix
        prefix += "".join(splits[:2])
        splits = splits[2:]

    return prev_prefix


def get_prefixes(files):
    matched = {}
    unmatched = files

    while len(unmatched):
        file = unmatched[0]
        splits = re.split(delimiters, file)

        prefix = find_prefix(splits, files)

        matched[prefix] = []
        for i in filter_start(unmatched, prefix):
            matched[prefix].append(i)
            unmatched.remove(i)

    return matched


def unwrap_path(path):
    dirs = list_dirs(path)
    files = list_files(path)

    if len(dirs) == 1 and len(files) == 0:
        return unwrap_path(path / dirs[0])
    return path


def finish_upload_(request, upload):
    error = lambda e: ([], [], [], [], [], e)
    uuid = str(upload.uuid)
    path = base_path
    path /= "file"
    path /= uuid

    for f in list_cleanup_files("file", str(upload.uuid), relative=False):
        os.remove(f)

    path = unwrap_path(path)
    dirs = list_dirs(path)
    files = list_files(path)

    if len(files) + len(dirs) == 0:
        return error("Nothing uploaded.")

    prefixes = {}
    if len(files) > 0:
        prefixes = get_prefixes(files)
        prefix = None, 0
        for k, v in prefixes.items():
            if len(v) > prefix[1]:
                prefix = k, len(v)

        prefix = prefix[0]
        files = []
        suffixes = []
        for f in prefixes[prefix]:
            suffixes.append(f[len(prefix) :])
            files.append(Path("<job>" + f[len(prefix) :]))

        file_suffixes = [re.sub("^" + delimiters + "+", "", s) for s in suffixes]

    if len(dirs) > 0:
        found = 0, None
        for d in dirs:
            dir_files = list_all_files(path / d)
            if len(dir_files) > found[0]:
                found = len(dir_files), dir_files

        dir_files = found[1]
        json_dump = json.dumps([str(f) for f in dir_files])
        dirs = list(
            filter(
                lambda i: json.dumps([str(f) for f in list_all_files(path / i)])
                == json_dump,
                dirs,
            )
        )

        dir_suffixes = [str(f).split("/")[-1] for f in dir_files]
        files += ["<job>" / f for f in dir_files]

    if len(dirs) == 0:
        return (
            to_file_tree(files),
            files,
            file_suffixes,
            dirs,
            prefixes,
            False,
        )
    if len(prefixes) == 0:
        return (
            to_file_tree(files),
            files,
            dir_suffixes,
            dirs,
            prefixes,
            False,
        )

    return error("Format not supported right now.")


def finish_upload(request, upload):
    tree, files, suffixes, dirs, prefixes, error = finish_upload_(request, upload)

    return {"tree": to_file_tree(files), "suffixes": suffixes, "error": error}


def move_file(path, upload_id, file, type, job, copy=False, remove_prefix=False):
    assert isinstance(file, str)

    from_path = path / file

    if remove_prefix:
        file = file.split("/")
        if file[-1].startswith(job):
            file[-1] = "file" + file[-1][len(job) :]
        file = "/".join(file)

    to_path = base_path / type / upload_id / (job + ".job") / file

    os.makedirs(to_path.parent, exist_ok=True)

    if copy:
        shutil.copy(from_path, to_path)
    else:
        move(from_path, to_path)


def finalize_upload(request, upload):
    uuid = str(upload.uuid)
    # avoid name duplicate if 'file' is part of the types
    tree, files, suffixes, dirs, prefixes, error = finish_upload_(request, upload)

    data = request.data
    manual_format = data.get("manual_format", False)
    checkboxes = data.get("checkboxes", [])
    types = data.get("types", [])

    len_suffixes = len(suffixes)
    len_types = len(types)

    path = base_path / "file" / (uuid + "_")
    move(base_path / "file" / uuid, path)
    path = unwrap_path(path)

    for prefix, files in prefixes.items():
        for file in files:
            longest_find = 0, 0
            for i in range(len_suffixes):
                if file.endswith(suffixes[i]):
                    if len(suffixes[i]) > longest_find[0]:
                        longest_find = len(suffixes[i]), i
            i = longest_find[1]

            for t in checkboxes[i]:
                type = types[t]
                move_file(
                    path,
                    uuid,
                    file,
                    type,
                    job=prefix,
                    copy=(t != checkboxes[i][-1]),
                    remove_prefix=True,
                )
    for dir in dirs:
        for i in range(len_suffixes):
            for t in checkboxes[i]:
                type = types[t]
                move_file(
                    path / dir,
                    uuid,
                    suffixes[i],
                    type,
                    job=dir,
                    copy=(t != checkboxes[i][-1]),
                )

    shutil.rmtree(base_path / "file" / (uuid + "_"))
    upload.is_finished = True
    upload.save()

    return 0


def copy_folder(inp_path, out_path):
    if ".." in inp_path:
        return
    if ".." in out_path:
        return

    path = Path(settings.DATA_PATH)
    for p in inp_path.split("/"):
        path /= p
    inp_path = path
    path = Path(settings.DATA_PATH)
    for p in out_path.split("/"):
        path /= p
    out_path = path

    os.makedirs(inp_path, exist_ok=True)
    os.makedirs(out_path, exist_ok=True)
    shutil.rmtree(out_path)

    shutil.copytree(inp_path, out_path)


def make_download_link(rel_path, name="download"):
    import random
    import string

    from_path = base_path
    for p in rel_path.split("/"):
        from_path /= p

    to_path = settings.DOWNLOADS_DIR
    folder = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))

    os.makedirs(os.path.join(to_path, folder), exist_ok=True)
    to_file = os.path.join(to_path, folder, name + ".tar.gz")

    subprocess.run(["tar", "-czvf", to_file, "-C", str(from_path), "."])

    Download(path=to_file).save()

    return settings.DOWNLOADS_URL + folder + "/" + name + ".tar.gz"

