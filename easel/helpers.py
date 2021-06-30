import json
import logging
import os
import os.path
from pathlib import Path

import markdown
import requests
import tinydb


API="/api/v1"
HTTPS="https://"
DIRS = { # maps a directory name to its easel module name
        "assignment_groups": "assignment_group",
        "assignments": "assignment",
        "external_tools": "external_tool",
        "files": "files",
        "modules": "module",
        "pages": "page",
        "quiz_questions": "quiz_question",
        "quizzes": "quiz",
        }

def md2html(mdtext):
    extensions = ['fenced_code', 'codehilite', 'tables']
    return markdown.markdown(mdtext, extensions=extensions)

def write_config(hostname, token, dry_run):
    home = Path.home()
    if home == "":
        raise ValueError("home directory is not set")

    config_file = home / ".easelrc" # https://docs.python.org/3.7/library/pathlib.html#operators

    config = {"hostname": hostname, "token": token}
    try:
        if dry_run:
            print(f"DRYRUN - writing to file {config_file}")
        else:
            with open(config_file, 'x') as f:
                f.write(json.dumps(config)) # TODO: 0644
    except FileExistsError:
        logging.error(f"Config file {config_file} exists")

def load_db():
    return tinydb.TinyDB(".easeldb", sort_keys=True, indent=4, separators=(',', ': '))

def setup_directories(dry_run):
    for d in DIRS:
        if not os.path.isdir(d):
            if dry_run:
                print(f"DRYRUN - mkdir {d}")
            else:
                print(f"Creating directory {d}")
                os.mkdir(d)

def delete(path, params={}, decode=True, dry_run=False):
    return do_request(path, params, "DELETE", dry_run=dry_run)

def get(path, params={}, decode=True, dry_run=False):
    return do_request(path, params, "GET", dry_run=dry_run)

def post(path, upload, params={}, dry_run=False):
    return do_request(path, params, "POST", upload, dry_run=dry_run)

def put(path, upload, params={}, dry_run=False):
    return do_request(path, params, "PUT", upload, dry_run=dry_run)

def do_request(path, params, method, upload=None, dry_run=False):
    if not path.startswith("/"):
        raise ValueError('request path must start with /')
    if method not in ('GET', 'POST', 'PUT', 'DELETE'):
        raise ValueError('do_request only recognizes GET, POST, PUT, and DELETE methods')

    conf = Config()
    headers={'Authorization': 'Bearer '+conf.token}
    req_url = "https://"+conf.hostname+path
    data = None
    if upload is not None and method in ('POST', 'PUT'):
        data = dict(upload)

    logging.info(f"{method} {req_url}")
    logging.debug(f"Params: {params}")
    logging.debug(f"Headers: {headers}")
    logging.debug("Data: {}".format(json.dumps(data, sort_keys=True, indent=4)))

    if dry_run:
        print("DRYRUN - making request (use --api or --api-dump for more details)")
        return {}

    # apparently requests can't handle nested dictionaries in the data
    # parameter so I'm using the json param for it instead
    resp = requests.request(method, req_url, params=params, json=data,
            headers=headers)

    r = ""
    if resp.text:
        r = resp.json()

    logging.debug(json.dumps(r, sort_keys=True, indent=4))
    if resp.status_code == 500:
        logging.error("Canvas did not like that request. Perhaps the component"
                " you are trying to push was incorrectly formatted. A common "
                "mistake is having a typo in the yaml. It might help to "
                "inspect the request parameters with the --api-dump flag.")
    if resp.status_code not in [200, 201, 204, 400, 404, 500]:
        raise requests.HTTPError("Received unexpected status: {}".format(resp.status_code))
    return r

class Config:

    def __init__(self):
        home = Path.home()
        if home == "":
            raise ValueError("home directory is not set")

        config_file = home / ".easelrc" # https://docs.python.org/3.7/library/pathlib.html#operators

        f = open(config_file)
        c = json.loads(f.read())
        f.close()
        self.hostname = c["hostname"]
        self.token = c["token"]

    def __repr__(self):
        return f"Config(hostname={self.hostname},  token={self.token})"
