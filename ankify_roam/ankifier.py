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


def ankify(pyroam, deck="Default", basic_model="Roam Basic", cloze_model="Roam Cloze", tag_ankify="anki_note", pageref_cloze="outside"): 
    logger.info("Fetching blocks to ankify")
    blocks_to_ankify = pyroam.query(lambda b: tag_ankify in b.get_tags(inherit=False))

    logger.info("Ankifying and uploading")
    block_ankifier = BlockAnkifier(deck, basic_model, cloze_model, pageref_cloze)
    for block in blocks_to_ankify:
        try:
            anki_note = block_ankifier.ankify(block, pageref_cloze=pageref_cloze)
        except:
            logging.exception(f"Failed ankifying {block} during conversion to anki note")
        else:
            try:
                anki.upload(anki_note)
            except:
                logging.exception(f"Failed ankifying {block} during upload to anki")


def ankify_from_file(path):
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


class BlockAnkifier:
    def __init__(self, deck="Default", basic_model="Roam Basic", cloze_model="Roam Cloze", pageref_cloze="outside"):
        self.deck = deck
        self.basic_model = basic_model
        self.cloze_model = cloze_model
        self.pageref_cloze = pageref_cloze
        self.field_names = {}

    def ankify(self, block, **kwargs):
        default_model = self.basic_model if self._get_type(block)=="basic" else self.cloze_model
        modelName = self._get_model(block) or default_model
        deckName = self._get_deck(block) or self.deck
        if modelName not in self.field_names.keys():
            self.field_names[modelName] = anki.get_field_names(modelName)
        fields = self._block_to_fields(block, self.field_names[modelName], **kwargs)
        tags = block.get_tags()
        return {
            "deckName": deckName,
            "modelName": modelName,
            "fields": fields,
            "tags": tags
        }

    def _get_model(self, block):
        # TODO
        return ""

    def _get_deck(self, block):
        # TODO
        return ""

    def _get_type(self, block):
        # TODO: extract type from tags
        if any([type(obj)==Cloze for obj in block.content]):
            return "cloze"
        else:
            return "basic"

    def _block_to_fields(self, block, field_names, **kwargs):
        if self._get_type(block)=="basic":
            blocks = [block, block.children] 
        else:
            blocks = [block]
        fields = {}
        for i, (fn, b) in enumerate(zip_longest(field_names, blocks)):
            kwargs["proc_cloze"] = i==0
            fields[fn] = b.to_html(**kwargs) if b else "" 
        if "uid" in field_names:
            fields["uid"] = block.uid
        return fields
