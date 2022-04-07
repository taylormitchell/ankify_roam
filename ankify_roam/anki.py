import json 
import urllib.request 
import logging
import traceback
import re

logger = logging.getLogger(__name__)

def connection_open():
    request = urllib.request.Request('http://localhost:8765', json.dumps({}).encode("utf-8"))
    try:
        response = json.load(urllib.request.urlopen(request))
    except urllib.request.URLError:
        return False
    return True

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

def upload_all(anki_dicts):
    for anki_dict in anki_dicts:
        upload(anki_dict)

def upload(anki_dict):
    note_id = get_note_id(anki_dict)
    if note_id:
        return update_note(anki_dict, note_id)
    else:
        return add_note(anki_dict)
            
def add_note(anki_dict):
    for image in anki_dict.pop("images", []):
        add_media(image)
    return _invoke("addNote", note=anki_dict)

def update_note(anki_dict, note_id=None):
    for image in anki_dict.pop("images", []):
        add_media(image)
    note_id = note_id or get_note_id(anki_dict)
    return update_fields(note_id, anki_dict["fields"])

def suspend_note(anki_dict):
    card_ids = get_card_ids(anki_dict)
    return _invoke("suspend", cards=card_ids)

def unsuspend_note(anki_dict):
    card_ids = get_card_ids(anki_dict)
    return _invoke("unsuspend", cards=card_ids)

def update_fields(note_id, fields):
    note = {"id":note_id, "fields": fields}
    return _invoke("updateNoteFields", note=note)

def add_media(media):
    return _invoke("storeMediaFile", **media)

def found_media(filename):
    try:
        res = _invoke("retrieveMediaFile", filename=filename)
        return True if res else False
    except Exception as e:
        logging.warning(f"Exception while looking for media: {e}")
        return False

def update_tags(note_id, tags):
    old_tags = get_note_tags(note_id)
    delete_tags(note_id, old_tags)
    add_tags(note_id, tags)

def delete_tags(note_id, tags):
    for tag in tags:
        _invoke("removeTags", notes=[note_id], tags=tag)

def add_tags(note_id, tags):
    for tag in tags:
        _invoke("addTags", notes=[note_id], tags=tag)

def get_field_names(note_type):
    return _invoke('modelFieldNames', modelName=note_type)

def get_note_id(anki_dict):
    res = _invoke('findNotes', query=f"uid:{anki_dict['fields']['uid']}")
    if res:
        return res[0]
    return None

def get_card_ids(anki_dict):
    res = _invoke('findCards', query=f"uid:{anki_dict['fields']['uid']}")
    return res

def get_note(note_id):
    res = _invoke("notesInfo", notes=[note_id])
    if res:
        return res[0]
    return None

def get_note_tags(note_id):
    note = get_note(note_id)
    return note.get("tags")

def get_model_names():
    return _invoke("modelNames")

def get_deck_names():
    return _invoke("deckNames")

def get_profiles():
    return _invoke("getProfiles")

def get_model_templates(name):
    return _invoke("modelTemplates", modelName=name)

def is_model_cloze(name):
    model_template = get_model_templates(name)
    for card_name, card_template in model_template.items():
        for field_name, field_template in card_template.items():
            if re.search("{{cloze:.*}}", field_template):
                return True
    return False

def create_model(model):
    return _invoke("createModel", **model) 

def update_model(model):
    card_templates = model["cardTemplates"]
    names = [ct.pop("Name") for ct in card_templates]
    model_template_update = {
        "name": model["modelName"],
        "templates": {
            name: card_template 
            for name, card_template in zip(names, card_templates)
            }
    }
    res_template = _invoke("updateModelTemplates", model=model_template_update)
    model_styling_update = {
        "name": model["modelName"],
        "css": model["css"]
    }
    res_styling = _invoke("updateModelStyling", model=model_styling_update)
    return [res_template, res_styling]

def get_model_styling(model_name):
    return _invoke("modelStyling", modelName=model_name)

def load_profile(name):
    return _invoke("loadProfile", name=name)

def create_deck(name):
    return _invoke("createDeck", deck=name)

def delete_deck(name, cards_too=True):
    return _invoke("deleteDecks", decks=[name], cardsToo=cards_too)

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
