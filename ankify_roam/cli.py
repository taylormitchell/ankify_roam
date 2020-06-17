import argparse
import inspect
from ankify_roam import ankifier 

def get_default_args(func):
    signature = inspect.signature(func)
    return {
        k: v.default
        for k, v in signature.parameters.items()
        if v.default is not inspect.Parameter.empty
    }

def ankify():
    default_args = get_default_args(ankifier.ankify)
    parser = argparse.ArgumentParser(description='Import flashcards from Roam to Anki')
    parser.add_argument('path',
                        metavar='path',
                        type=str,
                        help='the path to list')
    parser.add_argument('--deck', default=default_args['deck'],
                        type=str, action='store', 
                        help='default deck')
    parser.add_argument('--basic_model', default=default_args['basic_model'], 
                        type=str, action='store', 
                        help='default deck')
    parser.add_argument('--cloze_model', default=default_args['cloze_model'],
                        type=str, action='store', 
                        help='default deck')
    parser.add_argument('--pageref-cloze', default=default_args['pageref_cloze'],
                        type=str, action='store', 
                        choices=["inside", "outside", "base_only"],
                        help='where to place clozes around page references')
    parser.add_argument('--tag-ankify', default=default_args['tag_ankify'],
                        type=str, action='store', 
                        help='default deck')

    kwargs = vars(parser.parse_args())
    path = kwargs.pop("path")
    ankifier.ankify_from_file(path, **kwargs)

if __name__=="__main__":
    ankify()
