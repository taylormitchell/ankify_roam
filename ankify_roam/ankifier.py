import argparse
import os
import sys
import logging
import re
from itertools import zip_longest
from ankify_roam.roam import PyRoam, Cloze
from ankify_roam import anki

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def ankify(pyroam, deck="Default", basic_model="Roam Basic", cloze_model="Roam Cloze", tag_ankify="anki_note", pageref_cloze="outside"):
    logger.info("Fetching blocks to ankify")
    anki_blocks = pyroam.query(lambda b: tag_ankify in b.get_tags(inherit=False))

    field_names = {}
    try:
        basic_fields = anki.get_field_names(basic_model)
        cloze_fields = anki.get_field_names(cloze_model)
    except anki.ModelNotFoundError as e:
        raise anki.ModelNotFoundError(
            f"'{basic_model}' or '{cloze_model}' not in Anki. "\
            "Try running `setup_anki.py` then pass 'Roam Basic' and 'Roam Cloze' "\
            "to default_basic and default_cloze")

    logger.info("Converting blocks to anki notes")
    anki_notes = []
    for block in anki_blocks:
        try:
            anki_notes.append(AnkiNote.from_block(
                block, deck, basic_model, cloze_model, basic_fields, cloze_fields))
        except Exception as e:
            logging.exception(f"Failed to convert block '{block.uid}' to an AnkiNote")

    logger.info("Preparing for upload to anki")
    anki_dicts = []
    for an in anki_notes:
        try:
            anki_dicts.append(an.to_dict(pageref_cloze=pageref_cloze))
        except Exception as e:
            logging.exception(f"Failed to convert AnkiNote '{block.uid}' to a dictionary")

    logger.info("Uploading to anki")
    for anki_dict in anki_dicts:
        try:
            anki.upload(anki_dict)
        except:
            logging.exception(f"Failed to upload '{block.uid}' to anki")


def ankify_from_file(path, **kwargs):
    logger.info("Loading PyRoam")
    pyroam = PyRoam.from_path(path)
    ankify(pyroam, **kwargs)


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
                cloze_fields, [block], fillvalue="")}
        else:
            type = basic_model
            fields = {n:f for n,f in zip_longest(
                basic_fields, [block, block.children], fillvalue="")}
        return cls(type, fields, deck, block.get("uid"), block.get_tags())

