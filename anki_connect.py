import json 
import urllib.request 
import logging
import traceback

class AnkiConnectException(Exception):
    """Base class for exceptions in this module."""
    pass

class BadResponse(AnkiConnectException):
    def __init__(self, response, message):
        self.response = response
        self.message = message

class GenericResponseError(AnkiConnectException):
    def __init__(self, response_error):
        self.response_error = response_error

class ModelNotFoundError(AnkiConnectException):
    def __init__(self, response_error):
        self.response_error = response_error

class DuplicateError(AnkiConnectException):
    def __init__(self, response_error):
        self.response_error = response_error


# https://github.com/FooSoft/anki-connect#python
def _create_request_dict(action, **params):
    return {'action': action, 'params': params, 'version': 6}

def _invoke(action, **params):
    requestDict = _create_request_dict(action, **params)
    requestJson = json.dumps(requestDict).encode('utf-8')
    request = urllib.request.Request('http://localhost:8765', requestJson)
    response = json.load(urllib.request.urlopen(request))
    if len(response) != 2:
        raise BadResponse(response, 'response has an unexpected number of fields')
    if 'error' not in response:
        raise BadResponse(response, 'response is missing required error field')
    if 'result' not in response:
        raise BadResponse(response, 'response is missing required result field')
    if response['error'] is not None:
        if response['error'].startswith('model was not found'):
            raise ModelNotFoundError(response['error'])
        elif "cannot create note because it is a duplicate" in response['error']:
            raise DuplicateError(response['error'])
        else:
            raise GenericResponseError(response['error'])
    return response['result']


def upload_all(anki_notes):
    for anki_note in anki_notes:
        upload(anki_note)

def upload(anki_note):
    note_id = _get_note_id(anki_note)
    try:
        if note_id:
            return _update_note(note_id, anki_note)
        else:
            return _add_note(anki_note)
    except Exception as e:
        logging.warning(f"Encountered the following error while trying to upload uid='{anki_note['fields']['uid']}'")
        print(e)
        traceback.print_exc()
            
def _add_note(anki_note):
    return _invoke("addNote", note=anki_note)

def _update_note(note_id, anki_note):
    note = {"id":note_id, "fields": anki_note["fields"]}
    return _invoke("updateNoteFields", note=note)

def get_field_names(note_type):
    return _invoke('modelFieldNames', modelName=note_type)

def _get_note_id(anki_note):
    res = _invoke('findNotes', query=f"uid:{anki_note['fields']['uid']}")
    if res:
        return res[0]
    return None

def get_model_names():
    return _invoke("modelNames")

def create_model(model):
    return _invoke("createModel", **model) 

def update_model(model):
    model_template_update = {
        "name": model["modelName"],
        "templates": {t["Name"]: {"Front":t["Front"], "Back":["Back"]} 
                      for t in model["cardTemplates"]}
    }
    res_template = _invoke("updateModelTemplates", model=model_template_update)
    model_styling_update = {
        "name": model["modelName"],
        "css": model["css"]
    }
    res_styling = _invoke("updateModelStyling", model=model_styling_update)
    return [res_template, res_styling]
