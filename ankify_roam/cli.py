import argparse
from ankify_roam import ankifier 
from ankify_roam import config

def ankify():
    parser = argparse.ArgumentParser(description='Import flashcards from Roam to Anki')
    parser.add_argument('path',
                        metavar='path',
                        type=str,
                        help='the path to list')
    parser.add_argument('--deck', default=config.deck,
                        type=str, action='store', 
                        help='default deck')
    parser.add_argument('--basic_model', default=config.basic_model, 
                        type=str, action='store', 
                        help='default deck')
    parser.add_argument('--cloze_model', default=config.cloze_model,
                        type=str, action='store', 
                        help='default deck')
    parser.add_argument('--pageref-cloze', default=config.pageref_cloze,
                        type=str, action='store', 
                        choices=["inside", "outside", "base_only"],
                        help='where to place clozes around page references')
    parser.add_argument('--tag-ankify', default=config.tag_ankify,
                        type=str, action='store', 
                        help='default deck')

    args = vars(parser.parse_args())
    path = args.pop("path")
    ankifier.ankify_from_path(path, **args)
