import unittest
import json
import logging
import subprocess
import os
import psutil
from ankify_roam import roam, anki
from ankify_roam.tests.roam_export import ROAM_JSON
from ankify_roam.default_models import ROAM_BASIC, ROAM_CLOZE
from ankify_roam.ankifiers import RoamGraphAnkifier
from ankify_roam import util

class AnkiAppTest:
    @staticmethod
    def get_process():
        for process in psutil.process_iter():
            if process.name()=='Anki':
                return process

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
        import pdb; pdb.set_trace()
        if args["deck"] not in anki.get_deck_names():
            anki.create_deck(args["deck"])
        for model in [ROAM_BASIC, ROAM_CLOZE]:
            if not model['modelName'] in anki.get_model_names():
                anki.create_model(model)



class TestRoamGraphAnkifier(unittest.TestCase):
    def setUp(self):
        self.profile="test"
        self.deck="test"
        if not anki.load_profile(self.profile):
            raise ValueError("You need an anki profile called 'test' to run the Ankifier tests on")
        anki.delete_deck(self.deck)
        anki.create_deck(self.deck)

    def test_ankify(self):
        pages = json.loads(ROAM_JSON)
        roam_graph = roam.RoamGraph(pages)
        ankifier = RoamGraphAnkifier(deck=self.deck)
        with self.assertLogs() as ctx:
            ankifier.ankify(roam_graph)
        self.assertFalse([r for r in ctx.records if r.levelno >= logging.WARNING])

    #def test_setup_models(self):
    #    ankifier.setup_models()
    #    model_names = ROAM_BASIC['modelName'], ROAM_CLOZE['modelName']
    #    self.assertTrue(set(model_names).issubset(anki.get_model_names()))

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

    def test_bad_basic_model(self):
        if not AnkiAppTest.is_open():
            AnkiAppTest.open()
        ankifier = RoamGraphAnkifier(basic_model="not a model")
        with self.assertRaises(ValueError) as cm:
            ankifier.check_conn_and_params()
        self.assertEqual(
            f"Note type named '{ankifier.basic_model}' not in Anki.", 
            str(cm.exception))

    def test_bad_cloze_model(self):
        if not AnkiAppTest.is_open():
            AnkiAppTest.open()
        ankifier = RoamGraphAnkifier(cloze_model="not a model")
        with self.assertRaises(ValueError) as cm:
            ankifier.check_conn_and_params()
        self.assertEqual(
            f"Note type named '{ankifier.cloze_model}' not in Anki.", 
            str(cm.exception))

    def test_missing_uid_field(self):
        if not AnkiAppTest.is_open():
            AnkiAppTest.open()
        ankifier = RoamGraphAnkifier(basic_model="Basic")
        with self.assertRaises(ValueError) as cm:
            ankifier.check_conn_and_params()
        self.assertEqual(
            f"'{ankifier.basic_model}' note type is missing a 'uid' field.", 
            str(cm.exception))

    def test_cloze_not_cloze(self):
        if not AnkiAppTest.is_open():
            AnkiAppTest.open()
        ankifier = RoamGraphAnkifier(cloze_model="Roam Basic")
        with self.assertRaises(ValueError) as cm:
            ankifier.check_conn_and_params()
        self.assertEqual(
            f"cloze_model must be a cloze note type and '{ankifier.cloze_model}' isn't.", 
            str(cm.exception))


if __name__=="__main__":
    unittest.main()