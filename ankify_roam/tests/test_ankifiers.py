import unittest
import re
import json
import logging
import subprocess
import os
import psutil
from ankify_roam import roam, anki
from ankify_roam.tests.roam_export import ROAM_JSON
from ankify_roam.default_models import ROAM_BASIC, ROAM_CLOZE, add_default_models
from ankify_roam.ankifiers import RoamGraphAnkifier, BlockAnkifier
from ankify_roam.roam import Block, BlockContent
from ankify_roam import util

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
        anki.delete_deck(self.deck)
        anki.create_deck(self.deck)
        add_default_models(overwrite=True)

    def test_ankify(self):
        pages = json.loads(ROAM_JSON)
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


class TestBlockAnkifier(unittest.TestCase):
    def test_get_option(self):
        ankifier = BlockAnkifier()

        block = Block.from_string("a block #[[[[ankify_roam]]:note='Roam Basic']]")
        self.assertEqual(ankifier._get_option(block, 'note'), "Roam Basic")

        block = Block.from_string("a block #[[[[ankify]]:note='Roam Basic']]")
        self.assertEqual(ankifier._get_option(block, 'note'), "Roam Basic")

        block = Block.from_string("a block #[[ankify: note='Roam Basic']]")
        self.assertEqual(ankifier._get_option(block, 'note'), "Roam Basic")

        block = Block.from_string("a block #[[ankify: note=Roam Basic]]")
        self.assertEqual(ankifier._get_option(block, 'note'), "Roam Basic")

    def test_front_to_html(self):
        """
        - [[Page title]]
          - grandparent block
            - parent block
              - ankified block
        """
        block = Block.from_string("ankified block")
        block.parent_page = "Page title"
        block.parent_blocks = [Block.from_string("grandparent block"), Block.from_string("parent block")]

        # No parent blocks or page
        ankifier = BlockAnkifier(num_parents=0, include_page=False)
        expected = '<div class="front-side">ankified block</div>'
        self.assertEqual(ankifier.front_to_html(block), expected)

        # All parent blocks and page
        ankifier = BlockAnkifier(num_parents="all", include_page=True)
        expected = remove_html_whitespace("""
        <div class="front-side">
            <ul>
                <li class="page-title parent parent-3 parent-top">
                    <span data-link-title="Page title">
                    <span class="rm-page-ref-brackets">[[</span>
                    <span class="rm-page-ref rm-page-ref-link-color">Page title</span>
                    <span class="rm-page-ref-brackets">]]</span></span>
                </li>
                <ul>
                    <li class="block parent parent-2">grandparent block</li>
                    <ul>
                        <li class="block parent parent-1">parent block</li>
                        <ul>
                            <li class="block">ankified block</li>
                        </ul>
                    </ul>
                </ul>
            </ul>
        </div>
        """)
        self.assertEqual(ankifier.front_to_html(block), expected)

        # Some parent blocks and page
        ankifier = BlockAnkifier(num_parents=1, include_page=True)
        expected = remove_html_whitespace("""
        <div class="front-side">
            <ul>
                <li class="page-title parent parent-3 parent-top">
                    <span data-link-title="Page title">
                    <span class="rm-page-ref-brackets">[[</span>
                    <span class="rm-page-ref rm-page-ref-link-color">Page title</span>
                    <span class="rm-page-ref-brackets">]]</span></span>
                </li>
                <ul>
                    <li class="block parent parent-2"><span class="ellipsis">...</span></li>
                    <ul>
                        <li class="block parent parent-1">parent block</li>
                        <ul>
                            <li class="block">ankified block</li>
                        </ul>
                    </ul>
                </ul>
            </ul>
        </div>
        """)
        self.assertEqual(ankifier.front_to_html(block), expected)

    def test_back_to_html(self):
        block = Block.from_string("block with children")
        child1 = Block.from_string("child 1")
        grandchild1 = Block.from_string("grandchild 1")
        child2 = Block.from_string("child 2")

        # one child
        block.children = [child1]
        ankifier = BlockAnkifier()
        expected = '<div class="back-side">child 1</div>'
        self.assertEqual(ankifier.back_to_html(block), expected)

        # multiple children
        child1.children = [grandchild1]
        block.children = [child1, child2]
        ankifier = BlockAnkifier()
        expected = remove_html_whitespace("""
        <div class="back-side list">
            <ul>
                <li>child 1</li>
                <ul>
                    <li>grandchild 1</li>
                </ul>
                <li>child 2</li>
            </ul>
        </div>
        """)
        self.assertEqual(ankifier.back_to_html(block), expected)

        # max depth
        block.children = [child1, child2]
        ankifier = BlockAnkifier(max_depth=1)
        expected = remove_html_whitespace("""
        <div class="back-side list">
            <ul>
                <li>child 1</li>
                <li>child 2</li>
            </ul>
        </div>
        """)
        self.assertEqual(ankifier.back_to_html(block), expected)

    def test_ankify(self):
        block = Block(
            content=BlockContent.from_string("question"),
            children=[Block.from_string("answer")],
            parent_blocks=[],
            parent_page="page"
        )
        ankifier = BlockAnkifier(
            deck="my deck",
            note_basic="my basic",
            field_names = {"my basic": ["Front", "Back"]}
        )
        expected = {
            "deckName": "my deck",
            "modelName": "my basic",
            "fields": {
                "Front": '<div class="front-side">question</div>', 
                "Back": '<div class="back-side">answer</div>'
            },
            "tags": []
        }
        self.assertEqual(expected, ankifier.ankify(block))


def remove_html_whitespace(html_string):
    html_string = re.sub(">\s*\n?\s*<", "><", html_string)
    html_string = re.sub("^\s*\n?\s*", "", html_string)
    html_string = re.sub("\s*\n?\s*$", "", html_string)
    return html_string


if __name__=="__main__":
    unittest.main()