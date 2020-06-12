import json 
import urllib.request 
import logging
import traceback
import re
from itertools import zip_longest
from roam import PyRoam, Cloze

class AnkiNote:
    def __init__(self, type, fields, deck, uid="", tags=[]):
        self.type = type
        self.fields = fields
        self.uid = uid
        self.deck = deck
        self.roam_tags = tags

    def get_tags(self):
        return [re.sub("\s","_",tag) for tag in self.roam_tags]

    def to_dict(self, **kwargs):
        fields = {}
        for i, (field_name, field) in enumerate(self.fields.items()):
            proc_cloze = True if i==0 else False
            fields[field_name] = field.to_html(proc_cloze=proc_cloze, **kwargs) if field else ""
        if "uid" in self.fields.keys():
            fields["uid"] = self.uid
        return {
            "deckName": self.deck,
            "modelName": self.type,
            "fields": fields,
            "tags": self.get_tags()
        }

    @staticmethod
    def is_block_cloze(block):
        return any([type(obj)==Cloze for obj in block.content])

    @classmethod
    def from_block(cls, block, deck, basic_model, cloze_model, basic_fields, cloze_fields):
        """
        Args:
            block (BlockObject): 
            deck (str): Deck
            basic_model (str): Name of card type to upload basic cards to  
            cloze_model (str): Name of card type to upload cloze cards to  
            basic_fields (list of str): Field names of the basic card type
            cloze_fields (list of str): Field names of the cloze card type
        """
        if cls.is_block_cloze(block):
            type = cloze_model
            fields = {n:f for n,f in zip_longest(
                basic_fields, [block], fillvalue="")}
        else:
            type = basic_model
            fields = {n:f for n,f in zip_longest(
                basic_fields, [block, block.children], fillvalue="")}
        return cls(type, fields, deck, block.get("uid"), block.get_tags())

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
    note_id = _get_note_id(anki_dict)
    try:
        if note_id:
            return _update_note(note_id, anki_dict)
        else:
            return _add_note(anki_dict)
    except Exception as e:
        logging.warning(f"Encountered the following error while trying to upload uid='{anki_dict['fields']['uid']}'")
        print(e)
        traceback.print_exc()
            
def _add_note(anki_dict):
    return _invoke("addNote", note=anki_dict)

def _update_note(note_id, anki_dict):
    note = {"id":note_id, "fields": anki_dict["fields"]}
    return _invoke("updateNoteFields", note=note)

def get_field_names(note_type):
    return _invoke('modelFieldNames', modelName=note_type)

def _get_note_id(anki_dict):
    res = _invoke('findNotes', query=f"uid:{anki_dict['fields']['uid']}")
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
