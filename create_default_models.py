from model_templates import ROAM_BASIC, ROAM_CLOZE
import anki_connect

modelNames = anki_connect.get_model_names()
for model in [ROAM_BASIC, ROAM_CLOZE]:
    if not model['modelName'] in modelNames:
        anki_connect.create_model(model)
    else:
        anki_connect.update_model(model)

