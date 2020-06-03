import re
import logging
from roam import RoamDb
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
        fields = {fn:f.to_html(**kwargs) for fn,f in zip(field_names, self.fields)}
        if "uid" in field_names:
            fields["uid"] = self.uid
        return {
            "deckName": self.deck,
            "modelName": self.type,
            "fields": fields,
            "tags": self.get_tags()
        }

    @staticmethod
    def _extract_deck(block, default_deck):
        RE_DECK = r"\[\[anki_deck\]\]:(\w+)"
        for tag in block.get_tags():
            match = re.search(RE_DECK, tag)
            if match: break
        return match.group() if match else default_deck

    @staticmethod
    def _extract_type(block, default_basic, default_cloze):
        RE_TYPE = r"\[\[anki_type\]\]:(\w+)"
        for tag in block.get_tags():
            match = re.search(RE_TYPE, tag)
            if match: break
        if match:
            return match.group()
        else:
            RE_CLOZE = r"{[^{}]+}"
            if re.findall(RE_CLOZE, block.get("string")):
                return default_cloze
            else:
                return default_basic

    @classmethod
    def from_block(cls, block, default_deck, default_basic, default_cloze):
        deckName = cls._extract_deck(block, default_deck)
        type = cls._extract_type(block, default_basic, default_cloze)
        fields = [block, block.get("children")]
        return cls(type, fields, deckName, block.get("uid"), block.get_tags())
