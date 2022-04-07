import unittest
import json
from ankify_roam.roam.containers import RoamGraph, Page, Block 
from ankify_roam.roam.content import BlockContent


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
        with open("tests/export-pages.json") as f:
          pages = json.load(f)
        roam_graph = RoamGraph(pages)
        page = roam_graph.get_page("Geography")
        self.assertEqual(page.num_descendants(), 10)


class TestBlock(unittest.TestCase):
    def test_num_descendants(self):
        with open("tests/export-pages.json") as f:
          pages = json.load(f)
        roam_graph = RoamGraph(pages)
        block = roam_graph.query_by_uid("klGAc1Gi3")
        self.assertEqual(block.num_descendants(), 9)


class TestTagsFromAttribute(unittest.TestCase):
  def test_block(self):
    block = Block(
        content=BlockContent.from_string("some [[block]]"),
        children=[
            Block(BlockContent("another block")),
            Block(BlockContent.from_string("tags:: #[[foo]], [[bar]]"))
        ]
    )
    self.assertSetEqual(set(block.get_tags(from_attr=False)), set(["block"]))
    self.assertSetEqual(set(block.get_tags(from_attr=True)), set(["block", "foo", "bar"]))

  def test_page(self):
    page = Page(
        title = "derp",
        children = [
            Block(BlockContent("another [[block]]")),
            Block(BlockContent.from_string("tags:: #[[foo]], [[bar]]"))
        ]
    )
    self.assertSetEqual(set(page.get_tags(from_attr=False)), set(["derp"]))
    self.assertSetEqual(set(page.get_tags(from_attr=True)), set(["derp", "foo", "bar"]))


  
