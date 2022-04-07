import sys
import inspect
import argparse
import logging
import re
import os
import subprocess
from ankify_roam import __version__
from ankify_roam import anki
from ankify_roam.default_models import ROAM_BASIC, ROAM_CLOZE, add_default_models
from ankify_roam.ankifiers import RoamGraphAnkifier
from ankify_roam.roam import RoamGraph
from ankify_roam import util

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def add(path, **kwargs):
    logger.info("Setting up Ankifier")
    ankifier = RoamGraphAnkifier(**kwargs)
    ankifier.check_conn_and_params()
    logger.info("Loading Roam Graph")
    roam_graph = RoamGraph.from_path(path)
    ankifier.ankify(roam_graph)


def init_models(overwrite=False):
    models = add_default_models(overwrite=overwrite)
    for name, model in models.items():
        if model:
            logger.info(f"Added '{name}'")
        else:
            logging.info(
                f"'{name}' already in Anki. "\
                "If you want to overwrite it, use `ankify_roam init-models --overwrite`")


def get_version():
    try:
        res = subprocess.run(["git", "-C", os.path.dirname(__file__), "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True)
        if res.returncode == 0:
            # this is a local git repository
            git_branch = res.stdout.decode().strip()
            return __version__ + "+" + git_branch
    except:
        pass
    return __version__


def main():
    parser = argparse.ArgumentParser(
        description='Import flashcards from Roam to Anki',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--version', action='version',
                        version='%(prog)s {version}'.format(version=get_version()))

    subparsers = parser.add_subparsers(help='sub-command help')

    # Arguments for adder
    default_args = util.get_default_args(RoamGraphAnkifier.__init__)
    parser_add = subparsers.add_parser("add", 
        help='Add a Roam export to Anki',
        description='Add a Roam export to Anki')
    parser_add.add_argument('path',
                        metavar='path',
                        type=str,
                        help='path to the Roam export json or containing directory')
    parser_add.add_argument('--deck', default=default_args['deck'],
                        type=str, action='store', 
                        help='Deck to add notes to (default: "%(default)s")')
    parser_add.add_argument('--note-basic', default=default_args['note_basic'], 
                        type=str, action='store', 
                        help='Note type to assign basic flashcards (default: "%(default)s")')
    parser_add.add_argument('--note-cloze', default=default_args['note_cloze'],
                        type=str, action='store', 
                        help='Note type to assign cloze flashcards (default: "%(default)s")')
    parser_add.add_argument('--pageref-cloze', default=default_args['pageref_cloze'],
                        type=str, action='store', 
                        choices=["inside", "outside", "base_only"],
                        help='Where to place clozes around page references (default: "%(default)s")')
    parser_add.add_argument('--tag-ankify', default=default_args['tag_ankify'],
                        type=str, action='store', 
                        help='Roam tag used to flag blocks to ankify (default: "%(default)s")')
    parser_add.add_argument('--tag-dont-ankify', default=default_args['tag_dont_ankify'],
                        type=str, action='store', 
                        help='Roam tag used to flag blocks not to ankify, even if they have the `--tag-ankify` tag (default: "%(default)s")')
    parser_add.add_argument('--tag-ankify-root', default=default_args['tag_ankify_root'],
                        type=str, action='store', 
                        help='Roam tag used to treat a block as a root node, even if there are parents above it (default: "%(default)s")')
    parser_add.add_argument('--num-parents', default=default_args['num_parents'],
                        type=str, action='store', 
                        help='Number of parents blocks to include on anki notes (pass "all" to select all) (default: "%(default)s")')
    parser_add.add_argument('--include-page', default=default_args['num_parents'],
                        action='store_true', 
                        help='Whether to include page titles on anki notes')
    parser_add.add_argument('--tags-from-attr', default=default_args['tags_from_attr'],
                        action='store_true', 
                        help='Whether to assign tags next to "tags::" property to parent')
    parser_add.add_argument('--max-depth', default=default_args['max_depth'],
                        type=str, action='store', 
                        help="Maximum depth of children to ankify e.g. `--max-depth=1` will show the block's children but not grand children. (default: '%(default)s')")
    parser_add.add_argument('--download-imgs', default=default_args['download_imgs'],
                        type=str, action='store',
                        choices=["once", "always", "never"],
                        help='Whether to download images embedded in blocks and save in anki')
    parser_add.set_defaults(func=add)

    # Arguments for initializer
    parser_init = subparsers.add_parser("init-models", 
        help="Initialize Anki with default note types used by ankify_roam",
        description="Initialize Anki with Roam specific models")
    parser_init.add_argument('--overwrite', action="store_true", 
        help="whether to overwrite the models if they already exist")
    parser_init.set_defaults(func=init_models)

    args = vars(parser.parse_args())

    # If no arguments were given, print the help message and exit
    if len(args)==0:
        parser.print_help(sys.stderr)
        sys.exit(1)

    if args.get("num_parents"):
        try:
            args["num_parents"] = int(args["num_parents"])
        except ValueError:
            if args["num_parents"] != "all":
                raise ValueError("Invalid max-depth value")

    if args.get("max_depth"):
        if args["max_depth"]=="None":
            args["max_depth"] = None
        try:
            args["max_depth"] = int(args["max_depth"])
        except ValueError:
            raise ValueError("Invalid max-depth value")

    # Run ankify_roam
    func = args.pop("func")
    func(**args)

if __name__=="__main__":
    main()
