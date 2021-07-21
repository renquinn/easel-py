import json
import logging
import os
import os.path
import urllib.parse

import requests
from tqdm import tqdm

from easel import canvas_id
from easel import course
from easel import helpers

COURSE_FILES_PATH=course.COURSE_PATH+"/files"
COURSE_FOLDERS_PATH=course.COURSE_PATH+"/folders"
FILES_PATH=helpers.API+"/files"
FILE_PATH=FILES_PATH+"/{}"

def push(db, course_, component_filepath, hidden, dry_run):
    print(f"pushing File {component_filepath} to {course_.name} ({course_.canvas_id})")
    if os.path.isdir(component_filepath):
        pushdir(db, course_, component_filepath, hidden, dry_run)
    elif os.path.isfile(component_filepath):
        pushfile(db, course_, component_filepath, hidden, dry_run)
    else:
        logging.error("Invalid File type for " + component_filepath)

def pushdir(db, course_, dir_path, hidden, dry_run):
    for child_path in os.listdir(dir_path):
        push(db, course_, dir_path + '/' + child_path, hidden, dry_run)

def pushfile(db, course_, full_path, hidden, dry_run):
    parent_folder_path, name = os.path.split(full_path)
    if parent_folder_path[:5] == "files":
        parent_folder_path = parent_folder_path[5:]
    if parent_folder_path[:1] == "/":
        parent_folder_path = parent_folder_path[1:]

    # https://canvas.instructure.com/doc/api/file.file_uploads.html
    params = {
            "name": name,
            "size": os.path.getsize(full_path),
            "parent_folder_path": parent_folder_path,
            "publish": False,
            }
    # Step 1: Telling Canvas about the file upload and getting a token
    resp = helpers.post(COURSE_FILES_PATH.format(course_.canvas_id), params, dry_run=dry_run)

    # Step 2: Upload the file data to the URL given in the previous response
    if not dry_run and ("upload_url" not in resp or "upload_params" not in resp):
        logging.error("Invalid response received for file upload")
        print(resp)
        return

    file_ = {'file': open(full_path, 'rb')}
    req_url = resp.get('upload_url')
    params = resp.get("upload_params")
    logging.info(f"POST {req_url}")
    logging.debug(f"Params: {params}")
    logging.debug(f"File: {file_}")

    if dry_run:
        print("DRYRUN - making request (use --api or --api-dump for more details)")
    else:
        resp = requests.request("POST", req_url, params=params, files=file_)
        if resp.text:
            r = resp.json()
            logging.debug(json.dumps(r, sort_keys=True, indent=4))

            file_id = r.get('id')
            cid = canvas_id.CanvasID(full_path, course_.canvas_id)
            cid.canvas_id = file_id
            cid.save(db)

    # Step 3: Confirm the upload's success (requests follows redirects by
    # default, so far this has been enough to satisfy canvas)

    if hidden:
        r = helpers.put(FILE_PATH.format(file_id), {"hidden": True})
        if not r.get('hidden'):
            logging.error("TODO: failed to hide the file")

def remove(db, course_, component_filepath, dry_run):
    print(f"removing {component_filepath} from {course_.name} ({course_.canvas_id})")
    if os.path.isdir(component_filepath):
        removedir(db, course_, component_filepath, dry_run)
    elif os.path.isfile(component_filepath):
        removefile(db, course_, component_filepath, dry_run)
    else:
        logging.error("Invalid file type for " + component_filepath)

def removedir(db, course_, dir_path, dry_run):
    for child_path in os.listdir(dir_path):
        remove(db, course_, dir_path + '/' + child_path, dry_run)

def removefile(db, course_, full_path, dry_run):
    cid = canvas_id.CanvasID(full_path, course_.canvas_id)
    cid.find_id(db)
    if cid.canvas_id:
        r = helpers.delete(FILE_PATH.format(cid.canvas_id), dry_run=dry_run)
        if r.get('upload_status') == 'success':
            cid.remove(db)

def pull_file(db, course_id, url, id_, filepath):
    helpers.download_file(url, filepath)
    cid = canvas_id.CanvasID(filepath, course_id)
    cid.canvas_id = id_
    cid.save(db)
    return cid

def pull_all(db, course_, dry_run):
    r = helpers.get(COURSE_FOLDERS_PATH.format(course_.canvas_id),
            dry_run=dry_run)
    for folder in r:
        path = folder['full_name'][len("course "):]
        print(f"pulling list of files in {path}")
        os.makedirs(path, exist_ok=True)
        files_path = urllib.parse.urlparse(folder['files_url']).path
        r = helpers.get(files_path, dry_run=dry_run)
        print(f"downloading files in {path}")
        for file_ in tqdm(r):
            if 'filename' not in file_ or 'url' not in file_ or 'id' not in file_:
                logging.error("Invalid file response from canvas:")
                print(file_)
                continue
            filepath = path + '/' + file_['filename']
            pull_file(db, course_.canvas_id, file_['url'], file_['id'], filepath)
    # normally we'd return a list of file objects for diffing the local ones,
    # but since we don't track files in the db we won't be able to diff
    # anything (in the the way it's done in commands.py)
    # TODO: but it might be worth returning the contents of the files, although
    # we'd want to optimize for memory usage in case of large files
    return []
