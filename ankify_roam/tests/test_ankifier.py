import unittest
import json
import logging
from ankify_roam import ankifier
from ankify_roam import roam
from ankify_roam import anki
from ankify_roam.tests.roam_export import ROAM_JSON

class TestAnkify(unittest.TestCase):
    def test(self):
        anki.load_profile("test")
        pages = json.loads(ROAM_JSON)
        pyroam = roam.PyRoam(pages)
        with self.assertLogs() as ctx:
            ankifier.ankify(pyroam)
            #ankifier.main("ankify_roam/tests/test_export.json")
        self.assertFalse([r for r in ctx.records if r.levelno >= logging.WARNING])

if __name__=="__main__":
    unittest.main()