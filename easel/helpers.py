import json
import logging
import markdown
import os
from pathlib import Path
import requests
import tinydb


API="/api/v1"
HTTPS="https://"

def md2html(mdtext):
    extensions = ['fenced_code', 'codehilite', 'tables']
    return markdown.markdown(mdtext, extensions=extensions)

def write_config(hostname, token):
    home = Path.home()
    if home == "":
        raise ValueError("home directory is not set")

    config_file = home / ".easelrc" # https://docs.python.org/3.7/library/pathlib.html#operators

    config = {"hostname": hostname, "token": token}
    try:
        with open(config_file, 'x') as f:
            f.write(json.dumps(config)) # TODO: 0644
    except FileExistsError:
        logging.error(f"Config file {config_file} exists")

def load_db():
    return tinydb.TinyDB(".easeldb")

def setup_directories():
    dirs = ["assignment_groups", "assignments", "external_tools", "modules",
            "pages", "quizzes"]
    for d in dirs:
        try:
            os.mkdir(d)
        except FileExistsError:
            continue

def get(path, params={}, decode=True):
    return do_request(path, params, "GET")

def post(path, upload, params={}):
    return do_request(path, params, "POST", upload)

def put(path, upload, params={}):
    return do_request(path, params, "PUT", upload)

def do_request(path, params, method, upload=None):
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

    # apparently requests can't handle nested dictionaries in the data
    # parameter so I'm using the json param for it instead
    resp = requests.request(method, req_url, params=params, json=data,
            headers=headers)

    logging.debug(json.dumps(resp.json(), sort_keys=True, indent=4))
    if resp.status_code not in [200, 201]:
        raise requests.HTTPError("Received unexpected status: {}".format(resp.status_code))
    return resp.json()

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
