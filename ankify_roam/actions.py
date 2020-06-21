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

def add(pyroam, deck="Default", basic_model="Roam Basic", cloze_model="Roam Cloze", tag_ankify="ankify", pageref_cloze="outside"): 
    logger.info("Fetching blocks to ankify")
    blocks_to_ankify = pyroam.query(lambda b: tag_ankify in b.get_tags(inherit=False))

    logger.info(f"Ankifying and uploading {len(blocks_to_ankify)} blocks")
    block_ankifier = BlockAnkifier(deck, basic_model, cloze_model, pageref_cloze, tag_ankify)
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


def add_from_file(path, **kwargs):
    logger.info("Loading PyRoam")
    pyroam = PyRoam.from_path(path)
    add(pyroam, **kwargs)


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


def cli():
    def get_default_args(func):
        signature = inspect.signature(func)
        return {
            k: v.default
            for k, v in signature.parameters.items()
            if v.default is not inspect.Parameter.empty
        }
    parser = argparse.ArgumentParser(description='Import flashcards from Roam to Anki')
    subparsers = parser.add_subparsers(help='sub-command help')

    # initialize
    parser_init = subparsers.add_parser("init", 
        help="Initialize Anki with Roam specific models",
        description="Initialize Anki with Roam specific models")
    parser_init.add_argument('--overwrite', action="store_true", 
        help="whether to overwrite the models if they already exist")
    parser_init.set_defaults(func=setup_models)

    # add roam to anki
    default_args = get_default_args(add)
    parser_add = subparsers.add_parser("add", 
        help='Add a Roam export to Anki',
        description='Add a Roam export to Anki')
    parser_add.add_argument('path',
                        metavar='path',
                        type=str,
                        help='path to the Roam export file or containing directory')
    parser_add.add_argument('--deck', default=default_args['deck'],
                        type=str, action='store', 
                        help='default deck to add notes to')
    parser_add.add_argument('--basic_model', default=default_args['basic_model'], 
                        type=str, action='store', 
                        help='default model to assign basic cards')
    parser_add.add_argument('--cloze_model', default=default_args['cloze_model'],
                        type=str, action='store', 
                        help='default model to assign cloze cards')
    parser_add.add_argument('--pageref-cloze', default=default_args['pageref_cloze'],
                        type=str, action='store', 
                        choices=["inside", "outside", "base_only"],
                        help='where to place clozes around page references')
    parser_add.add_argument('--tag-ankify', default=default_args['tag_ankify'],
                        type=str, action='store', 
                        help='Roam tag used to identify blocks to ankify')
    parser_add.set_defaults(func=add_from_file)

    args = vars(parser.parse_args())
    func = args.pop("func")
    func(**args)

if __name__=="__main__":
    cli()
