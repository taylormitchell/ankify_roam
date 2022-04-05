import unittest
from ankify_roam import anki, roam, default_models
from ankify_roam.ankifiers import RoamGraphAnkifier
from ankify_roam.default_models import ROAM_BASIC, ROAM_CLOZE, add_default_models
import subprocess
import os
import psutil
import json
import logging


class AnkiAppTest:
    @staticmethod
    def get_process():
        # source: https://psutil.readthedocs.io/en/latest/#find-process-by-name
        for p in psutil.process_iter(['name']):
            if p.info['name'] in ["Anki", "AnkiMac"]:
                return p

    @classmethod
    def is_open(cls):
        if cls.get_process():
            return True
        return False

    @classmethod
    def close(cls):
        process = cls.get_process()
        if process:
            process.kill()
        while cls.is_open():
            pass

    @classmethod
    def open(cls):
        if not cls.is_open():
            subprocess.call(["open","/Applications/Anki.app/"])
        while not anki.connection_open():
            pass
        anki.load_profile("test")

    @classmethod
    def setup(cls):
        args = util.get_default_args(RoamGraphAnkifier.__init__)
        if args["deck"] not in anki.get_deck_names():
            anki.create_deck(args["deck"])
        for model in [ROAM_BASIC, ROAM_CLOZE]:
            if not model['modelName'] in anki.get_model_names():
                anki.create_model(model)


class TestRoamGraphAnkifier(unittest.TestCase):
    def setUp(self):
        if not AnkiAppTest.is_open():
            AnkiAppTest.open()
        self.profile="test"
        self.deck="test"
        if not anki.load_profile(self.profile):
            raise ValueError("You need an anki profile called 'test' to run the Ankifier tests on")
        # anki.delete_deck(self.deck)
        # anki.create_deck(self.deck)
        # add_default_models(overwrite=True)

    def test_ankify(self):
        with open("tests/roam_export.json") as f:
            pages = json.load(f)
        roam_graph = roam.RoamGraph(pages)
        ankifier = RoamGraphAnkifier(deck=self.deck)
        with self.assertLogs() as ctx:
            ankifier.ankify(roam_graph)
        self.assertFalse([r for r in ctx.records if r.levelno >= logging.WARNING])


class TestCheckConnAndParams(unittest.TestCase):
    def test_no_anki_conn(self):
        if AnkiAppTest.is_open():
            AnkiAppTest.close()
        ankifier = RoamGraphAnkifier()
        with self.assertRaises(ValueError) as cm:
            ankifier.check_conn_and_params()
        self.assertEqual("Couldn't connect to Anki.", str(cm.exception))

    def test_bad_deck(self):
        if not AnkiAppTest.is_open():
            AnkiAppTest.open()
        ankifier = RoamGraphAnkifier(deck="not a deck")
        with self.assertRaises(ValueError) as cm:
            ankifier.check_conn_and_params()
        self.assertEqual(
            f"Deck named '{ankifier.deck}' not in Anki.", 
            str(cm.exception))

    def test_bad_note_basic(self):
        if not AnkiAppTest.is_open():
            AnkiAppTest.open()
        ankifier = RoamGraphAnkifier(note_basic="not a model")
        with self.assertRaises(ValueError) as cm:
            ankifier.check_conn_and_params()
        self.assertEqual(
            f"Note type named '{ankifier.note_basic}' not in Anki.", 
            str(cm.exception))

    def test_bad_note_cloze(self):
        if not AnkiAppTest.is_open():
            AnkiAppTest.open()
        ankifier = RoamGraphAnkifier(note_cloze="not a model")
        with self.assertRaises(ValueError) as cm:
            ankifier.check_conn_and_params()
        self.assertEqual(
            f"Note type named '{ankifier.note_cloze}' not in Anki.", 
            str(cm.exception))

    def test_missing_uid_field(self):
        if not AnkiAppTest.is_open():
            AnkiAppTest.open()
        ankifier = RoamGraphAnkifier(note_basic="Basic")
        with self.assertRaises(ValueError) as cm:
            ankifier.check_conn_and_params()
        self.assertEqual(
            f"'{ankifier.note_basic}' note type is missing a 'uid' field.", 
            str(cm.exception))

    def test_cloze_not_cloze(self):
        if not AnkiAppTest.is_open():
            AnkiAppTest.open()
        ankifier = RoamGraphAnkifier(note_cloze="Roam Basic")
        with self.assertRaises(ValueError) as cm:
            ankifier.check_conn_and_params()
        self.assertEqual(
            f"note_cloze must be a cloze note type and '{ankifier.note_cloze}' isn't.", 
            str(cm.exception))


class TestAnki(unittest.TestCase):
    def setUp(self):
        if not AnkiAppTest.is_open():
            AnkiAppTest.open()
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


if __name__=="__main__":
    unittest.main()