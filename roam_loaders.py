import os
import re
import json
from zipfile import ZipFile

def loader(path):
    path = os.path.expanduser(path)
    if os.path.isdir(path):
        return latest_zip_export(path)
    elif os.path.splitext(path)[-1]==".zip":
        return zip_export(path)
    elif os.path.splitext(path)[-1]==".json":
        return json_export(path)
    else:
        raise ValueError

def latest_zip_export(path):
    roam_exports = [f for f in os.listdir(path) if re.match("Roam-Export-.*", f)]
    filename = sorted(roam_exports)[-1]
    roam_pages = zip_export(os.path.join(path, filename))

    return roam_pages


def zip_export(path):
    with ZipFile(path, 'r') as zip_ref:
        filename = zip_ref.namelist()[0]
        with zip_ref.open(filename) as f:
            roam_pages = json.load(f)

    return roam_pages


def json_export(path):
    with open(path) as f:
        roam_pages = json.load(f)
    
    return roam_pges

