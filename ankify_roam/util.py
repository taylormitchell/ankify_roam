import inspect
import anki

def get_default_args(func):
    signature = inspect.signature(func)
    return {
        k: v.default
        for k, v in signature.parameters.items()
        if v.default is not inspect.Parameter.empty
    }


def add_default_models():
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

if __name__=="__main__":
    add_default_models()