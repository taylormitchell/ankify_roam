import sys
import inspect
import argparse
import logging
import re
from ankify_roam import __version__
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


def update_models():
    modelNames = anki.get_model_names()
    for model in [ROAM_BASIC, ROAM_CLOZE]:
        if model['modelName'] in modelNames:
            anki.update_model(model)
            logger.info(f"Updated '{model['modelName']}'")
        else:
            logging.info(
                f"Model '{model['modelName']}' wasn't updated because it's missing from Anki. "\
                "See the README for instructions on how to add the model.")


def main():
    parser = argparse.ArgumentParser(description='Import flashcards from Roam to Anki')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {version}'.format(version=__version__))

    subparsers = parser.add_subparsers(help='sub-command help')

    # Arguments for update-model
    parser_update_model = subparsers.add_parser("update-models", 
        help="Update Roam specific models in Anki",
        description="Update Roam specific models in Anki")
    parser_update_model.set_defaults(func=update_models)

    # Arguments for initializer
    parser_init = subparsers.add_parser("init", 
        help="Initialize Anki with Roam specific models",
        description="Initialize Anki with Roam specific models")
    parser_init.add_argument('--overwrite', action="store_true", 
        help="whether to overwrite the models if they already exist")
    parser_init.set_defaults(func=init)

    # Arguments for adder
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
    parser_add.add_argument('--show-parents', default=default_args['show_parents'],
                        type=str, action='store', 
                        help='Whether to display block parents on the flashcard.')
    parser_add.add_argument('--max-depth', default=default_args['max_depth'],
                        type=str, action='store', 
                        help='Maximum depth of children to ankify')
    parser_add.set_defaults(func=add)
    args = vars(parser.parse_args())

    # If no arguments were given, print the help message and exit
    if len(args)==0:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # Process argument values
    if type(args.get("show_parents"))==str:
        if args["show_parents"]=="False":
            args["show_parents"] = False
        elif args["show_parents"]=="True":
            args["show_parents"] = True
        elif re.match("^([1-9]?\d+|0)$", args["show_parents"]):
            args["show_parents"] = int(args["show_parents"])
        else:
            raise ValueError("Invalid show-parents value")

    if type(args.get("max_depth"))==str:
        if args["max_depth"]=="None":
            args["max_depth"] = None
        elif re.match("^([1-9]?\d+|0)$", args["max_depth"]):
            args["max_depth"] = int(args["max_depth"])
        else:
            raise ValueError("Invalid max-depth value")

    # Run ankify_roam
    func = args.pop("func")
    func(**args)

if __name__=="__main__":
    main()
