import re
import logging
from itertools import zip_longest
from roam import RoamDb, Cloze
import anki_connect

class AnkiNote:
    def __init__(self, type, fields, deck, uid="", tags=[]):
        self.type = type
        self.fields = fields
        self.uid = uid
        self.deck = deck
        self.roam_tags = tags

    def get_tags(self):
        return [re.sub("\s","_",tag) for tag in self.roam_tags]

    def to_dict(self, field_names, **kwargs):
        fields = {}
        for i, (field_name, field) in enumerate(zip_longest(field_names, self.fields, fillvalue="")):
            proc_cloze = True if i==0 else False
            fields[field_name] = field.to_html(proc_cloze=proc_cloze, **kwargs) if field else field
        if "uid" in field_names:
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
    def from_block(cls, block, default_deck, default_basic, default_cloze):
        if cls.is_block_cloze(block):
            type = default_cloze
            fields = [block]
        else:
            type = default_basic
            fields = [block, block.get("children")]
        return cls(type, fields, default_deck, block.get("uid"), block.get_tags())
