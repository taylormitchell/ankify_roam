import argparse
import os
import sys
import logging
import re
import inspect
import string
from itertools import zip_longest
from ankify_roam.roam import PyRoam, Cloze
from ankify_roam import anki
from ankify_roam.default_models import ROAM_BASIC, ROAM_CLOZE 

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

ASCII_NON_PRINTABLE = "".join([chr(i) for i in range(128) 
                               if chr(i) not in string.printable])

class RoamGraphAnkifier:
    def __init__(self, deck="Default", basic_model="Roam Basic", cloze_model="Roam Cloze", pageref_cloze="outside", tag_ankify="ankify"):
        self.deck = deck
        self.basic_model = basic_model
        self.cloze_model = cloze_model
        self.pageref_cloze = pageref_cloze
        self.tag_ankify = tag_ankify

    def ankify(self, roam_graph):
        logger.info("Fetching blocks to ankify")
        blocks_to_ankify = roam_graph.query(lambda b: self.tag_ankify in b.get_tags(inherit=False))

        logger.info(f"Ankifying and uploading {len(blocks_to_ankify)} blocks")
        block_ankifier = BlockAnkifier(self.deck, self.basic_model, self.cloze_model, 
                                       self.pageref_cloze, self.tag_ankify)
        for block in blocks_to_ankify:
            try:
                anki_note = block_ankifier.ankify(block, pageref_cloze=self.pageref_cloze)
            except:
                logging.exception(f"Failed ankifying {block} during conversion to anki note")
                continue
            try:
                anki.upload(anki_note)
            except:
                logging.exception(f"Failed ankifying {block} during upload to anki")


class BlockAnkifier:
    def __init__(self, deck="Default", basic_model="Roam Basic", cloze_model="Roam Cloze", pageref_cloze="outside", tag_ankify="ankify"):
        self.deck = deck
        self.basic_model = basic_model
        self.cloze_model = cloze_model
        self.pageref_cloze = pageref_cloze
        self.tag_ankify = tag_ankify
        self.field_names = {}

    def ankify(self, block, **kwargs):
        modelName = self._get_model(block)
        deckName = self._get_deck(block)
        if modelName not in self.field_names.keys():
            self.field_names[modelName] = anki.get_field_names(modelName)
        model_type = self._get_model_type(modelName)
        fields = self._block_to_fields(block, self.field_names[modelName], model_type, **kwargs)
        tags = block.get_tags()
        return {
            "deckName": deckName,
            "modelName": modelName,
            "fields": fields,
            "tags": tags
        }

    def _get_model(self, block):
        # Search for assigned model
        pat = f"""^\[\[{self.tag_ankify}\]\]:model=([\w\s]*)$"""
        for tag in block.get_tags():
            m = re.match(pat, tag)
            if m:
                return m.group(1)
        # Otherwise infer from cloze markup
        if any([type(obj)==Cloze for obj in block.content]):
            return self.cloze_model
        else:
            return self.basic_model

    def _get_deck(self, block):
        pat = f"^\[\[{self.tag_ankify}\]\]:deck=(\w+)$"
        for tag in block.get_tags():
            m = re.match(pat, tag)
            if m:
                return m.group(1)
        return self.deck

    def _get_model_type(self, modelName):
        # Infer from blocks assigned model name 
        if re.search("[Cc]loze", modelName):
            return "cloze"
        else:
            return "basic"

    def _block_to_fields(self, block, field_names, model_type, **kwargs):
        if model_type=="basic":
            blocks = [block, block.children] 
            pc = lambda i: False
        else:
            blocks = [block]
            pc = lambda i: i==0
        fields = {}
        for i, (fn, b) in enumerate(zip_longest(field_names, blocks)):
            kwargs["proc_cloze"] = pc(i)
            text = b.to_html(**kwargs) if b else "" 
            text = re.sub("[%s]" % ASCII_NON_PRINTABLE, "", text)
            fields[fn] = text
        if "uid" in field_names:
            fields["uid"] = block.uid
        return fields

