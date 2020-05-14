import re
import os
import json
import sys
import urllib.request
import logging
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

RE_FIELD = r"#?\[\[\[\[anki_field\]\]:(\w+)\]\]"
RE_NOTE = r"#?\[\[anki_note\]\]|#anki_note"
RE_UID = r"#?\[\[\[\[uid\]\]:\({0,2}(\w+)\){0,2}\]\]"
RE_CLOZE_GROUPS = r"{(c?\d*):?([^:{}]*)}"
RE_CLOZE = r"{c?\d*:?[^:{}]*}"
RE_ANKI_TYPE = r"#?\[\[\[\[anki_type\]\]:(\w+)]\]"
RE_IMAGE = r"!\[\]\(([^()]*)\)"
RE_ANKI_DECK = r"#?\[\[\[\[anki_deck\]\]:(\w+)]\]"
RE_PAGE_REF_ONLY = "^\s*\[\[([^\[\]]*)\]\]\s*$"
RE_PAGE_REF = "\[\[([^\[\]]*)\]\]"
RE_BLOCK_REF = "\(\(([-_\w]+)\)\)"
RE_CODE_INLINE = r"`([^`]*)`"

# Roam Stuff
# ----------

class Roam:
    def __init__(self, pages):
        self.pages = pages
        self.block_strings = self.get_all_block_string(pages)
        
    def get_all_block_string(self, blocks, block_strings={}):
        for block in blocks:
            if block.get("uid"):
                block_strings[block["uid"]] = block["string"]
            block_strings = self.get_all_block_string(block.get('children',[]), block_strings)
        return block_strings
    
    def expand_block_refs(self, string):
        block_refs = re.findall(RE_BLOCK_REF, string)
        expanded_block_ref = []
        for ref in block_refs:
            if self.block_strings.get(ref):
                ref_sub = self.expand_block_refs(self.block_strings[ref])
            else:
                ref_sub = f"(({ref}))"
            string = string.replace(f"(({ref}))",ref_sub)
        return string
    
    def get_by_uid(self, uid):
        return self.get_by_criteria(lambda b: b["uid"]==uid)
            
    def get_by_criteria(self, criteria):
        for page in self.pages:
            block = self._get_block(criteria, page.get("children",[]))
            if block:
                return block
            
    def get_all_by_criteria(self, criteria):
        blocks = []
        for page in self.pages:
            blocks += self._get_all_blocks(page.get("children",[]), criteria)
        
        return blocks
            
    def _get_all_blocks(self, blocks, criteria):
        blocks_match = []
        for block in blocks:
            if criteria(block):
                blocks_match.append(block)
            blocks_match += self._get_all_blocks(block.get('children',[]), criteria)
        return blocks_match
        
    def _get_block(self, hook, blocks):
        if blocks is None:
            return None
        for block in blocks:
            if block.get("uid") and hook(block):
                return block
            block = self._get_block(hook, block.get("children"))
            if block:
                return block
        return block

    @classmethod
    def from_json(cls, path_to_json):
        with open(path_to_json) as f:
            pages = json.load(f)
        return cls(pages)


from enum import Enum, auto
class NoteType(Enum):
    BASIC = 0
    CLOZE = 1
    
class RoamNote:
    def __init__(self, block):
        self.uid = block["uid"]
        self.deck = self._get_deck(block)
        self.type = self._get_type(block)
        self.fields = self._get_fields(block, self.type)
        
    def _get_type(self, block):
        types = re.findall(RE_ANKI_TYPE, block["string"])
        if len(types) > 1:
            raise ValueError(f"Found {len(types)} note types. There shouldn't be more than 1.")
        # Use the type assigned with a tag if there is one. 
        if types:
            if types[0]=="Cloze":
                return NoteType.CLOZE
            elif types[0]=="Basic":
                return NoteType.BASIC
            else:
                pass
        # Otherwise infer the note type
        if re.findall(RE_CLOZE, block["string"]):
            return NoteType.CLOZE
        else:
            return NoteType.BASIC
        
    def _get_deck(self, block):
        decks = re.findall(RE_ANKI_DECK, block['string'])
        if len(decks) > 1:
            raise ValueError(f"Found {len(types)} note types. There shouldn't be more than 1.")
        if decks:
            return decks[0]
        return None
    
    def _get_fields(self, block, note_type):
        if note_type==NoteType.CLOZE:
            return [block["string"]]
        elif note_type==NoteType.BASIC:
            front = block["string"]
            back = block["children"][0]["string"] if block.get("children") else ""
            return [front, back]
        else:
            raise ValueError("Unknown note type")
        
    def __repr__(self):
        return f"<RoamNote(uid={self.uid}, type={self.type}, field[0]='{self.fields[0][:20]}...')>"
            
class RoamField:
    def __init__(self, block):
        self.text = block["string"]
        self.name = self._get_field_name(block)
        self.uids = self._get_uids(block)
        
    def _get_uids(self, block):
        return re.findall(RE_UID, block['string'])

    def _get_field_name(self, block):
        field_names = re.findall(RE_FIELD, block['string'])
        if len(field_names) > 1:
            raise ValueError(f"There should only be 1 field name but found {len(field_names)}")
        return field_names[0]
    
    def __repr__(self):
        return f"<RoamField(name={self.name}, text='{self.text[:20]}...')>"

# Anki Stuff
# ----------

from collections import OrderedDict
class AnkiNote:
    def __init__(self, modelName, field_names, deckName=""):
        self.deckName = deckName
        self.modelName = modelName
        self.fields = OrderedDict()
        for field_name in field_names:
            self.fields[field_name] = ""
        
    def set_field_by_index(self, index, text):
        key = list(self.fields.keys())[index]
        self.fields[key] = text
        
    def get_field_by_index(self, index):
        key = list(self.fields.keys())[index]
        return self.fields[key]
    
    def get_field(self, key):
        return self.fields[key]
    
    def to_dict(self):
        return self.__dict__
        
    def __repr__(self):
        name, text = list(self.fields.items())[0]
        return f"<AnkiNote {name}: '{text}'>"
    
    def __repr__(self):
        return f"<AnkiNote(uid={self.fields['uid']}, "\
               f"type={self.modelName}, "\
               f"field[0]='{self.get_field_by_index(0)[:20]}...')>"

class Roam2Anki:
    def __init__(self, roam, anki_connect, anki_basic="Roam Basic", anki_cloze="Roam Cloze", default_deck="Default"):
        self.roam = roam
        self.anki_connect = anki_connect
        self.anki_basic = anki_basic
        self.anki_cloze = anki_cloze
        self.default_deck = default_deck
        self.anki_field_names = {
            NoteType.BASIC: anki_connect.get_field_names(anki_basic),
            NoteType.CLOZE: anki_connect.get_field_names(anki_cloze)
        }

    def upload_all(self):
        roam_notes, roam_fields = self.get_notes_and_fields_from_roam()
        anki_notes = self.ankify_all(roam_notes, roam_fields)
        self.upload(anki_notes)

    def upload(self, anki_notes):
        responses = []
        for anki_note in anki_notes:
            responses.append(self.anki_connect.add_or_update_note(anki_note))
        return responses

    def get_notes_and_fields_from_roam(self):
        note_blocks = self.roam.get_all_by_criteria(lambda b: re.findall(RE_NOTE, b["string"]))
        field_blocks = self.roam.get_all_by_criteria(lambda b: re.findall(RE_FIELD, b["string"]))
        # Get all the juicy metadata from the blocks
        roam_notes = [RoamNote(block) for block in note_blocks]
        roam_fields = [RoamField(block) for block in field_blocks]

        return roam_notes, roam_fields

    def ankify_all(self, roam_notes, roam_fields):
        anki_notes = []
        for roam_note in roam_notes:
            additional_fields = []
            for roam_field in roam_fields:
                if roam_note.uid in roam_field.uids:
                    additional_fields.append(roam_field)
            anki_note = self.ankify(roam_note, additional_fields)
            anki_notes.append(anki_note)
        return anki_notes

    def ankify(self, roam_note, roam_fields=[]):
        anki_note = self._create_empty_note(roam_note.type)
        anki_note.deckName = roam_note.deck or self.default_deck
        anki_note.fields["uid"] = roam_note.uid
        self._add_fields(anki_note, roam_note, roam_fields)
        for name, field in anki_note.fields.items():
            anki_note.fields[name] = self._process_field(field, roam_note.type)
            
        return anki_note
    
    def _add_fields(self, anki_note, roam_note, roam_fields):
        for i,field in enumerate(roam_note.fields):
            anki_note.set_field_by_index(i, field)
        for field in roam_fields:
            anki_note.fields[field.name] = field.text


    def _add_uid(self, anki_note, roam_note):
        anki_note.fields["uid"] = roam_note.uid
        
    def _process_field(self, field, note_type):
        field = self._process_images(field)
        field = self._process_code(field)
        field = self._remove_tags(field)
        field = self._expand_block_refs(field)
        if note_type==NoteType.CLOZE:
            field = self._process_clozes(field)
        field = self._process_page_refs(field)
        return field

    def _process_images(self, field):
        return re.sub(RE_IMAGE, '<img src="\g<1>">', field)

    def _process_page_refs(self, field):
        sub = \
            '<span class="rm-page-ref-brackets">[[</span>'\
            '<span class="rm-page-ref-link-color">\g<1></span>'\
            '<span class="rm-page-ref-brackets">]]</span>'
        return re.sub(RE_PAGE_REF, sub, field) 
    
    def _remove_tags(self, field):
        for anki_tag in [RE_FIELD, RE_NOTE, RE_ANKI_TYPE, RE_UID, RE_ANKI_DECK]:
            field = re.sub(anki_tag,"",field)
        field = re.sub(r"\s+$","",field)
        return field

    def _process_code(self, field):
        return re.sub(RE_CODE_INLINE, "<code>\g<1></code>", field)
    
    def _expand_block_refs(self, field):
        return self.roam.expand_block_refs(field)
    
    def _process_clozes(self, field):
        clozes = re.findall(RE_CLOZE, field)
        # When cloze brackets surround a namespace page reference,  
        # move the brackets so they only surround the name.  
        new_clozes = []
        for cloze in clozes:
            cloze_key, cloze_text = cloze[1:-1].split(":")
            if re.match(RE_PAGE_REF_ONLY, cloze_text) and ("/" in cloze_text):
                page_name = re.findall(RE_PAGE_REF_ONLY, cloze_text)[0]
                namespace_split = page_name.split("/")
                clozed_name = "{%s:%s}" % (cloze_key, namespace_split[-1])
                new_cloze = "[[%s]]" % '/'.join(namespace_split[:-1] + [clozed_name])
                new_clozes.append(new_cloze)
            else:
                new_clozes.append(cloze)
        for cloze, new_cloze in zip(clozes, new_clozes):
            field = field.replace(cloze, new_cloze)
        # Change the cloze markup to the anki syntax 
        field = re.sub(RE_CLOZE_GROUPS, "{{\g<1>::\g<2>}}", field)
        
        return field
            
    def _create_empty_note(self, note_type):
        return AnkiNote(self._roam_type_to_anki(note_type), 
                        self.anki_field_names[note_type])
    
    def _roam_type_to_anki(self, note_type):
        if note_type==NoteType.BASIC:
            return self.anki_basic
        elif note_type==NoteType.CLOZE:
            return self.anki_cloze
        else:
            raise ValueError(f"Note type '{note_type}' not supported")

# AnkiConnect
# -----------            

#class AnkiConnect:
#    def add_all_notes(self, anki_notes):
#        for anki_note in anki_notes:
#            print(anki_note)
#
#    def get_field_names(self, note_type):
#        if note_type=='Roam Basic':
#            return ['Front','Back','Extra','uid']
#        else:
#            return ['Text','Extra','uid']

class AnkiConnect:
    def __init__(self):
        pass
    
    def add_or_update_note(self, anki_note):
        note_id = self.get_note_id(anki_note)
        if note_id:
            return self.update_note(note_id, anki_note)
        else:
            return self.add_note(anki_note)
                
    def add_note(self, anki_note):
        return self._invoke("addNote", note=anki_note.to_dict())

    def update_note(self, note_id, anki_note):
        note = {"id":note_id, "fields": anki_note.to_dict()["fields"]}
        return self._invoke("updateNoteFields", note=note)
    
    def get_field_names(self, note_type):
        return self._invoke('modelFieldNames', modelName=note_type)
    
    def get_note_id(self, anki_note):
        res = self._invoke('findNotes', query=f"uid:{anki_note.fields['uid']}")
        if res:
            return res[0]
        return None

    # https://github.com/FooSoft/anki-connect#python
    def _create_request_dict(self, action, **params):
        return {'action': action, 'params': params, 'version': 6}

    def _invoke(self, action, **params):
        requestDict = self._create_request_dict(action, **params)
        requestJson = json.dumps(requestDict).encode('utf-8')
        request = urllib.request.Request('http://localhost:8765', requestJson)
        response = json.load(urllib.request.urlopen(request))
        if len(response) != 2:
            raise Exception('response has an unexpected number of fields')
        if 'error' not in response:
            raise Exception('response is missing required error field')
        if 'result' not in response:
            raise Exception('response is missing required result field')
        if response['error'] is not None:
            raise Exception(response['error'])
        return response['result']


if __name__=="__main__":
    # User Input
    anki_basic = "Roam Basic"
    anki_cloze = "Roam Cloze"
    default_deck = "Default"
    path_to_json = os.path.expanduser(sys.argv[1])
    #path_to_json = os.path.expanduser("~/Downloads/roam_to_anki_test_page.json")

    logging.info("Starting")
    my_roam = Roam.from_json(path_to_json)
    anki_connect = AnkiConnect()
    roam2anki = Roam2Anki(my_roam, anki_connect, anki_basic=anki_basic, anki_cloze=anki_cloze, default_deck=default_deck)
    roam2anki.upload_all()
    logging.info("Finished")
