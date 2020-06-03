import argparse
import os
import sys
import logging
import anki_connect
import loaders 
from roam import RoamDb
from ankifier import AnkiNote
from model_templates import ROAM_BASIC, ROAM_CLOZE

if __name__=="__main__":
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    parser = argparse.ArgumentParser(description='Import flashcards from Roam to Anki')
    parser.add_argument('Path',
                        metavar='path',
                        type=str,
                        help='the path to list')
    #parser.add_argument('--input', 
    #                    action='store', default="json", 
    #                    choices=['json','zip','zip_latest'],
    #                    help='input type')
    parser.add_argument('--default_deck', default="Default",
                        type=str, action='store', 
                        help='default deck')
    parser.add_argument('--default_basic', default=ROAM_BASIC['modelName'], 
                        type=str, action='store', 
                        help='default deck')
    parser.add_argument('--default_cloze', default=ROAM_CLOZE['modelName'],
                        type=str, action='store', 
                        help='default deck')
    parser.add_argument('--images', default="download",
                        type=str, action='store', 
                        choices=["download","link"],
                        help='default deck')
    parser.add_argument('--uncloze-namespace', 
                        action='store_true',
                        help='move clozes surrounding namespaced pages to the base name') 

    args = parser.parse_args()

    logging.info("Starting")
    pages = loaders.loader(args.Path)
    logging.info("Loaded pages")

    roam_db = RoamDb.from_json(pages)
    logging.info("Placed into roam classes")

    anki_blocks = roam_db.get_blocks_by_tag("anki_note")
    logging.info("Fetched anki_note blocks")

    anki_notes = [AnkiNote.from_block(b, args.default_deck, args.default_basic, args.default_cloze) for b in anki_blocks]
    logging.info("Converted to anki notes")

    field_names = {}
    for model_name in [args.default_basic, args.default_cloze]:
        try:
            field_names[model_name] = anki_connect.get_field_names(model_name)
        except anki_connect.ModelNotFoundError as e:
            if model_name in [ROAM_BASIC['modelName'],ROAM_BASIC['modelName']]:
                # TODO: make sure this is the actual function name I'm using
                raise anki_connect.ModelNotFoundError(f"'{model_name}' not in Anki. Running `create_default_models.py` should fix the problem")
            else:
                raise e

    anki_dicts = [an.to_dict(field_names[an.type]) for an in anki_notes]

    anki_connect.upload_all(anki_dicts)

