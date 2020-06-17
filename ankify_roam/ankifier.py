import argparse
import os
import sys
import logging
import re
from itertools import zip_longest
from ankify_roam.roam import PyRoam, Cloze
from ankify_roam import anki
from ankify_roam.default_models import ROAM_BASIC, ROAM_CLOZE 

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class Ankifier:
    def __init__(self, deck="Default", basic_model="Roam Basic", cloze_model="Roam Cloze", tag_ankify="anki_note", pageref_cloze="outside"):
        self.deck = deck
        self.basic_model = basic_model
        self.cloze_model = cloze_model
        self.tag_ankify = tag_ankify
        self.pageref_cloze = pageref_cloze
        self.field_names = {}

    def ankify(self, pyroam): 
        logger.info("Fetching blocks to ankify")
        blocks_to_ankify = pyroam.query(lambda b: self.tag_ankify in b.get_tags(inherit=False))

        logger.info("Converting blocks to anki notes")
        anki_notes = []
        for block in blocks_to_ankify:
            try:
                anki_notes.append(self.block_to_anki_note(AnkiBlock(block)))
            except:
                logging.exception(f"Failed to convert block uid='{block.uid}' into an anki note")

        logger.info("Uploading to anki")
        for anki_dict in anki_dicts:
            try:
                anki.upload(anki_dict)
            except:
                logging.exception(f"Failed to upload '{block.uid}' to anki")

    def block_to_anki_note(self, block):
        field_names = {}
        default_model = self.basic_model if block.type=="basic" else self.cloze_model
        modelName = block.model or default_model
        deckName = block.deck or default_deck
        if modelName not in self.field_names.keys():
            field_names[modelName] = anki.get_field_names(modelName)
        fields = block.create_fields(field_names[modelName])
        tags = block.tags()
        return {
            "deckName": deckName,
            "modelName": modelName,
            "fields": fields,
            "tags": tags
        }

    def ankify_from_file(self, path):
        logger.info("Loading PyRoam")
        pyroam = PyRoam.from_path(path)
        ankify(pyroam)

def setup_models(overwrite=False):
    modelNames = anki.get_model_names()
    for model in [ROAM_BASIC, ROAM_CLOZE]:
        if not model['modelName'] in modelNames:
            anki.create_model(model)
        else:
            if overwrite:
                anki.update_model(model)
            else:
                logging.info(
                    f"'{model['modelName']}' already in Anki. "\
                    "If you want to overwrite it, set `overwrite=True`")

class AnkiBlock:
    def __init__(self, block, type="", deck=""):
        self.block = block

    @property
    def tags(self): return [re.sub("\s","_",tag) for tag in self.block.get_tags()]
    @property
    def uid(self): return self.block.uid

    @property
    def type(self):
        # TODO: extract type from tags
        if any([type(obj)==Cloze for obj in self.block.content]):
            return "cloze"
        else:
            return "basic"

    def model(self):
        # TODO: extract model name from tags
        return ""

    @property
    def deck(self): 
        # TODO: extract deck name from tags
        return ""

    def create_fields(self, field_names, **kwargs):
        if self.type=="basic":
            blocks = [self.block, self.block.children] 
        else:
            blocks = [self.block]
        fields = {}
        for i, (fn, block) in enumerate(zip_longest(field_names, blocks)):
            kwargs["proc_cloze"] = i==0
            fields[fn] = block.to_html(**kwargs) if block else "" 
        if "uid" in field_names:
            fields["uid"] = self.uid
        return fields
