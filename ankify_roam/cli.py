import inspect
import argparse
import logging
from ankify_roam import anki
from ankify_roam.default_models import ROAM_BASIC, ROAM_CLOZE
from ankify_roam.ankifiers import RoamGraphAnkifier
from ankify_roam.roam import RoamGraph
from ankify_roam import util

logger = logging.getLogger(__name__)

def add(path, **kwargs):
    logger.info("Setting up Ankifier")
    ankifier = RoamGraphAnkifier(**kwargs)
    ankifier.check_conn_and_params()
    logger.info("Loading Roam Graph")
    roam_graph = RoamGraph.from_path(path)
    ankifier.ankify(roam_graph)

def init(overwrite=False):
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

def main():
    parser = argparse.ArgumentParser(description='Import flashcards from Roam to Anki')
    subparsers = parser.add_subparsers(help='sub-command help')

    # initialize
    parser_init = subparsers.add_parser("init", 
        help="Initialize Anki with Roam specific models",
        description="Initialize Anki with Roam specific models")
    parser_init.add_argument('--overwrite', action="store_true", 
        help="whether to overwrite the models if they already exist")
    parser_init.set_defaults(func=init)

    # add roam to anki
    default_args = util.get_default_args(RoamGraphAnkifier.__init__)
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
    parser_add.add_argument('--note-basic', default=default_args['note_basic'], 
                        type=str, action='store', 
                        help='default note type to assign basic flashcards')
    parser_add.add_argument('--note-cloze', default=default_args['note_cloze'],
                        type=str, action='store', 
                        help='default note type to assign cloze flashcards')
    parser_add.add_argument('--pageref-cloze', default=default_args['pageref_cloze'],
                        type=str, action='store', 
                        choices=["inside", "outside", "base_only"],
                        help='where to place clozes around page references')
    parser_add.add_argument('--tag-ankify', default=default_args['tag_ankify'],
                        type=str, action='store', 
                        help='Roam tag used to identify blocks to ankify')
    parser_add.add_argument('--tag-dont-ankify', default=default_args['tag_dont_ankify'],
                        type=str, action='store', 
                        help='Roam tag used to identify blocks not to ankify')
    parser_add.set_defaults(func=add)

    args = vars(parser.parse_args())
    func = args.pop("func")
    func(**args)

if __name__=="__main__":
    main()