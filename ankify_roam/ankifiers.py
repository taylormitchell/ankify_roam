import argparse
import os
import sys
import logging
import re
import inspect
import string
from itertools import zip_longest
from ankify_roam import roam
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
        
    def check_conn_and_params(self):
        if not anki.connection_open():
            raise ValueError("Couldn't connect to Anki.") 
        if not self.deck in anki.get_deck_names():
            raise ValueError(f"Deck named '{self.deck}' not in Anki.")
        if not self.basic_model in anki.get_model_names():
            raise ValueError(f"Note type named '{self.basic_model}' not in Anki.")
        if not self.cloze_model in anki.get_model_names():
            raise ValueError(f"Note type named '{self.cloze_model}' not in Anki.")
        if not "uid" in anki.get_field_names(self.basic_model):
            raise ValueError(f"'{self.basic_model}' note type is missing a 'uid' field.")
        if not "uid" in anki.get_field_names(self.cloze_model):
            raise ValueError(f"'{self.cloze_model}' note type is missing a 'uid' field.")
        if not {'Cloze'} == anki.get_model_templates(self.cloze_model).keys():
            raise ValueError(f"cloze_model must be a cloze note type and '{self.cloze_model}' isn't.")



    def ankify(self, roam_graph):
        self.check_conn_and_params()
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
        if any([type(obj)==roam.Cloze for obj in block.content]):
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
        if model_type=="cloze":
            htmls = [block.to_html(**kwargs)]
        else:
            htmls = self.basic_to_htmls(block, **kwargs)
        fields = {fn: re.sub("[%s]" % ASCII_NON_PRINTABLE, "", html)
                  for fn, html in zip_longest(field_names, htmls, fillvalue="")}
        if "uid" in field_names:
            fields["uid"] = block.uid
        return fields


    def basic_to_htmls(self, block, **kwargs):
        htmls = [block.to_html(**kwargs)]
        children = block.children
        if len(children)==0: 
            htmls.append("")
        elif len(children)==1:
            htmls.append(children[0].to_html(proc_cloze=False, **kwargs))
        else:
            html = self._listify(children, proc_cloze=False, **kwargs)
            #TODO: should this be a config?
            htmls.append('<div class="centered-children">' + html + '</div>')
        return htmls

    def _listify(self, blocks, **kwargs):
        if blocks is None:
            return ""
        html = ""
        for block in blocks:
            content = block.to_html(**kwargs) + \
                      self._listify(block.get("children"))
            html += "<li>" + content + "</li>"
        html = "<ul>" + html + "</ul>"
        return html


        