import unittest
from ankify_roam import anki
from ankify_roam import default_models


class TestAnki(unittest.TestCase):
    def setUp(self):
        self.profile="test"
        self.deck="test"
        if not anki.load_profile(self.profile):
            raise ValueError("You need an anki profile called 'test' to run the Ankifier tests on")
        self.test_model_basic = {
            "modelName": "test_model_basic",
            "inOrderFields": ["Front", "Back", "Extra", "uid"],
            "css": "",
            "cardTemplates": [
                {
                    "Name": "Card 1",
                    "Front": "{{Front}}",
                    "Back": "{{FrontSide}}<hr id=answer>{{Back}}<br><br>{{Extra}}"
                }
            ]   
        }
        self.test_model_cloze = {
            "modelName": "test_model_cloze",
            "inOrderFields": ["Text", "Extra", "uid"],
            "css": "",
            "cardTemplates": [
                {
                    "Name": "Card 1",
                    "Front": "{{cloze:Text}}",
                    "Back": "{{cloze:Text}}<br><br>{{Extra}}"
                }
            ]   
        }

    def test_update_model(self):
        for test_model in [self.test_model_basic, self.test_model_cloze]:
            test_model = test_model.copy()
            # Create a model in anki
            modelNames = anki.get_model_names()
            while test_model["modelName"] in modelNames:
                test_model["modelName"] += "_1"
            anki.create_model(test_model)
            # Change the model's css then update it
            test_model["css"] = "test"
            anki.update_model(test_model)

            css = anki.get_model_styling(test_model["modelName"])["css"]
            self.assertEqual(test_model["css"], css)



        #model_cloze = {
        #    "modelName": "Roam Cloze",
        #    "inOrderFields": ["Text", "Extra", "uid"],
        #    "css": _css_cloze+_css_roam,
        #    "cardTemplates": [
        #        {
        #            "Name": "Card 1",
        #            "Front": "{{cloze:Text}}",
        #            "Back": "{{cloze:Text}}<br><br>{{Extra}}"
        #        }
        #    ]   
        #}


if __name__=="__main__":
    unittest.main()