import argparse
import os
import sys
import logging
from roam import PyRoam
import anki
from anki import AnkiNote
from model_templates import ROAM_BASIC, ROAM_CLOZE

if __name__=="__main__":
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    parser = argparse.ArgumentParser(description='Import flashcards from Roam to Anki')
    parser.add_argument('Path',
                        metavar='path',
                        type=str,
                        help='the path to list')
    parser.add_argument('--default_deck', default="Default",
                        type=str, action='store', 
                        help='default deck')
    parser.add_argument('--default_basic', default=ROAM_BASIC['modelName'], 
                        type=str, action='store', 
                        help='default deck')
    parser.add_argument('--default_cloze', default=ROAM_CLOZE['modelName'],
                        type=str, action='store', 
                        help='default deck')
    parser.add_argument('--pageref-cloze', default="outside",
                        type=str, action='store', 
                        choices=["inside", "outside", "base_only"],
                        help='where to place clozes around page references')
    parser.add_argument('--tag', default="anki_note",
                        type=str, action='store', 
                        help='default deck')

    args = parser.parse_args()

    logging.info("Loading PyRoam")
    pyroam = PyRoam.from_path(args.Path)

    logging.info("Fetching blocks to ankify")
    anki_blocks = pyroam.query(lambda b: args.tag in b.get_tags(inherit=False))

    field_names = {}
    try:
        basic_fields = anki.get_field_names(args.default_basic)
        cloze_fields = anki.get_field_names(args.default_cloze)
    except anki.ModelNotFoundError as e:
        raise anki.ModelNotFoundError(
            f"'{args.default_basic}' or '{args.default_cloze}' not in Anki. "\
            "Try running `setup_anki.py` then pass 'Roam Basic' and 'Roam Cloze' "\
            "to default_basic and default_cloze")

    logging.info("Converting blocks to anki notes")
    anki_notes = [AnkiNote.from_block(
        b, args.default_deck, args.default_basic, args.default_cloze, 
        basic_fields, cloze_fields) for b in anki_blocks]

    logging.info("Uploading to anki")
    anki_dicts = [an.to_dict(pageref_cloze=args.pageref_cloze) for an in anki_notes]
    anki.upload_all(anki_dicts)

