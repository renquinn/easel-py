import json
import logging
import os
import os.path
from pathlib import Path
import re
from tqdm import tqdm
import urllib.parse

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
        "local": "",
        }

def isurl(url):
    # requires protocol in addition to hostname
    try:
        parsed = urllib.parse.urlparse(url)
        return all([parsed.scheme, parsed.netloc])
    except:
        return False

def make_nested_filename(parent, child):
    return f"{parent}--{child}"

def filter_canvas_html(html):
    if not html:
        return html
    linktags = re.findall("<link.*?>", html)
    for lt in linktags:
        if 'canvas_global_app' in lt:
            html = html.replace(lt, '')
    scripttags = re.findall("<script.*?><\/script>", html)
    for st in scripttags:
        if 'canvas_global_app' in st:
            html = html.replace(st, '')
    return html

def md2html(mdtext):
    extensions = ['fenced_code', 'codehilite', 'tables', 'attr_list']
    config = {'codehilite': {'noclasses': True}}
    return markdown.markdown(mdtext, extensions=extensions,
            extension_configs=config)

def write_config(hostname, token, dry_run):
    home = Path.home()
    if home == "":
        raise ValueError("home directory is not set")

    config_file = home / ".easelrc" # https://docs.python.org/3.7/library/pathlib.html#operators

    config = {"hostname": hostname, "token": token}
    if os.path.isfile(config_file):
        resp = input(f"Config file {config_file} exists. Overwrite? [y/n] ")
        if resp != "y":
            print("Aborted.")
            return False

    if dry_run:
        print(f"DRYRUN - writing {config} to file {config_file}")
    else:
        with open(config_file, 'w') as f:
            f.write(json.dumps(config, indent=4))
    return True

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


    # make the request in a loop in case the response is paginated
    # https://canvas.instructure.com/doc/api/file.pagination.html
    results = []
    progress_bar = None
    while True:
        # apparently requests can't handle nested dictionaries in the data
        # parameter so I'm using the json param for it instead
        resp = requests.request(method, req_url, params=params, json=data,
                headers=headers)

        if resp.status_code == 500:
            logging.error("Canvas did not like that request. Perhaps the component"
                    " you are trying to push was incorrectly formatted. A common "
                    "mistake is having a typo in the yaml. It might help to "
                    "inspect the request parameters with the --api-dump flag.")
        if resp.status_code not in [200, 201, 204, 400, 404, 500]:
            raise requests.HTTPError("Received unexpected status: {}".format(resp.status_code))

        # check for pagination
        if 'next' in resp.links:
            if not results:
                last_page = int(urllib.parse.parse_qs(urllib.parse.urlparse(resp.links['last']['url']).query)['page'][0])
                progress_bar = tqdm(total=last_page)
                progress_bar.update()
            req_url = resp.links['next']['url']
            r = resp.json()
            logging.debug(json.dumps(r, sort_keys=True, indent=4))
            results += r
            progress_bar.update()
        else:
            if 'application/json' in resp.headers.get('content-type', ''):
                if len(results) == 0:
                    # not paginated
                    results = resp.json()
                    logging.debug(json.dumps(results, sort_keys=True, indent=4))
                    if 'errors' in results:
                        for err in results['errors']:
                            if isinstance(err, dict):
                                logging.error("Canvas Error: " + err.get('message'))
                            else:
                                logging.error("Canvas Error: " + str(err))
                else:
                    # the last page
                    r = resp.json()
                    logging.debug(json.dumps(r, sort_keys=True, indent=4))
                    results += r
                    progress_bar.update()
            break

    if progress_bar:
        progress_bar.close()

    return results

def download_file(url, filename):
    resp = requests.get(url, stream=True)
    resp.raise_for_status()
    f = open(filename, 'wb')
    for chunk in resp.iter_content(chunk_size=None):
        if chunk:
            f.write(chunk)
    f.close()

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
