import argparse
import os
import sys
import logging
from ankify_roam.roam import PyRoam
from ankify_roam import anki
from ankify_roam.anki import AnkiNote
from ankify_roam import config  

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def ankify(pyroam, **kwargs):
    deck = kwargs.get("deck", config.deck )
    basic_model = kwargs.get("basic_model", config.basic_model )
    cloze_model = kwargs.get("cloze_model", config.cloze_model )
    pageref_cloze = kwargs.get("pageref_cloze", config.pageref_cloze )
    tag_ankify = kwargs.get("tag_ankify", config.tag_ankify )

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
    anki_notes = [AnkiNote.from_block(
        b, deck, basic_model, cloze_model, 
        basic_fields, cloze_fields) for b in anki_blocks]

    logger.info("Uploading to anki")
    anki_dicts = [an.to_dict(pageref_cloze=pageref_cloze) for an in anki_notes]

    anki.upload_all(anki_dicts)

def ankify_from_path(path, **kwargs):
    logger.info("Loading PyRoam")
    pyroam = PyRoam.from_path(path)
    ankify(pyroam, **kwargs)


