import unittest
import json
from ankify_roam.roam.containers import RoamGraph, Page, Block 
from ankify_roam.tests.roam_export import ROAM_JSON

class TestRoamGraph(unittest.TestCase):
    def setUp(self):
        pages = [ 
            {
              "title": "test page for [[ankify_roam]]",
              "children": [
                {
                  "string": "{{[[TODO]]}} has some blocks with [[page]] [links]([[temp]])",
                  "create-email": "taylor.j.mitchell@gmail.com",
                  "create-time": 1591572843972,
                  "children": [
                    {
                      "string": "some have children #tag ",
                      "create-email": "taylor.j.mitchell@gmail.com",
                      "create-time": 1591572870827,
                      "uid": "5xB8JO-xg",
                      "edit-time": 1591572883462,
                      "edit-email": "taylor.j.mitchell@gmail.com"
                    }
                  ],
                  "uid": "YlgtAqOYv",
                  "edit-time": 1591572870832,
                  "edit-email": "taylor.j.mitchell@gmail.com"
                },
                {
                  "string": "It's got some queries: {{query:{and:[[TODO]][[test page for [[ankify_roam]]]]}}}",
                  "create-email": "taylor.j.mitchell@gmail.com",
                  "create-time": 1591572883456,
                  "uid": "_xUQrzbZY",
                  "edit-time": 1591572918548,
                  "edit-email": "taylor.j.mitchell@gmail.com"
                },
                {
                  "string": "Some block refs: ((5xB8JO-xg)) #temp ",
                  "create-email": "taylor.j.mitchell@gmail.com",
                  "create-time": 1591572908104,
                  "uid": "L7EuhRiXa",
                  "edit-time": 1591572963120,
                  "edit-email": "taylor.j.mitchell@gmail.com"
                }
              ],
              "edit-time": 1591572842475,
              "edit-email": "taylor.j.mitchell@gmail.com"
            }
        ]
        self.roam_db = RoamGraph(pages)

    def test_get_tags(self):
        block = self.roam_db.query_by_uid("L7EuhRiXa")
        a = set(block.get_tags())
        b = set(["temp","test page for [[ankify_roam]]"])
        self.assertSetEqual(a,b)

        block = self.roam_db.query_by_uid("YlgtAqOYv")
        a = set(block.get_tags())
        b = set(["TODO","page","temp","test page for [[ankify_roam]]"])
        self.assertSetEqual(a,b)


class TestPage(unittest.TestCase):
    def test_num_descendants(self):
        pages = json.loads(ROAM_JSON)
        roam_graph = RoamGraph(pages)
        page = roam_graph.get_page("Geography")
        self.assertEquals(page.num_descendants(), 9)


class TestBlock(unittest.TestCase):
    def test_num_descendants(self):
        pages = json.loads(ROAM_JSON)
        roam_graph = RoamGraph(pages)
        block = roam_graph.query_by_uid("klGAc1Gi3")
        self.assertEquals(block.num_descendants(), 8)