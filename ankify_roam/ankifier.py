import argparse
import os
import sys
import logging
from ankify_roam.roam import PyRoam
from ankify_roam import anki
from ankify_roam.anki import AnkiNote
from ankify_roam.model_templates import ROAM_BASIC, ROAM_CLOZE

DEFAULT_DECK = "Default"
DEFAULT_BASIC = "Roam Basic"
DEFAULT_CLOZE = "Roam Cloze"
PAGEREF_CLOZE = "outside"
TAG_ANKIFY = "anki_note"

# Set up the root logger
logger_root = logging.getLogger()
logger_root.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('error.log', mode='w')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger_root.addHandler(fh)
logger_root.addHandler(ch)


def main(
    path, 
    default_deck=DEFAULT_DECK, 
    default_basic=DEFAULT_BASIC, 
    default_cloze=DEFAULT_CLOZE, 
    pageref_cloze=PAGEREF_CLOZE, 
    tag_ankify=TAG_ANKIFY):

    logger = logging.getLogger(__name__)

    logger.info("Loading PyRoam")
    pyroam = PyRoam.from_path(path)

    logger.info("Fetching blocks to ankify")
    anki_blocks = pyroam.query(lambda b: tag_ankify in b.get_tags(inherit=False))

    field_names = {}
    try:
        basic_fields = anki.get_field_names(default_basic)
        cloze_fields = anki.get_field_names(default_cloze)
    except anki.ModelNotFoundError as e:
        raise anki.ModelNotFoundError(
            f"'{default_basic}' or '{default_cloze}' not in Anki. "\
            "Try running `setup_anki.py` then pass 'Roam Basic' and 'Roam Cloze' "\
            "to default_basic and default_cloze")

    logger.info("Converting blocks to anki notes")
    anki_notes = [AnkiNote.from_block(
        b, default_deck, default_basic, default_cloze, 
        basic_fields, cloze_fields) for b in anki_blocks]

    logger.info("Uploading to anki")
    anki_dicts = [an.to_dict(pageref_cloze=pageref_cloze) for an in anki_notes]

    anki.upload_all(anki_dicts)


if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Import flashcards from Roam to Anki')
    parser.add_argument('path',
                        metavar='path',
                        type=str,
                        help='the path to list')
    parser.add_argument('--default_deck', default=DEFAULT_DECK,
                        type=str, action='store', 
                        help='default deck')
    parser.add_argument('--default_basic', default=DEFAULT_BASIC, 
                        type=str, action='store', 
                        help='default deck')
    parser.add_argument('--default_cloze', default=DEFAULT_CLOZE,
                        type=str, action='store', 
                        help='default deck')
    parser.add_argument('--pageref-cloze', default=PAGEREF_CLOZE,
                        type=str, action='store', 
                        choices=["inside", "outside", "base_only"],
                        help='where to place clozes around page references')
    parser.add_argument('--tag-ankify', default=TAG_ANKIFY,
                        type=str, action='store', 
                        help='default deck')

    args = parser.parse_args()
    main(**vars(args))


