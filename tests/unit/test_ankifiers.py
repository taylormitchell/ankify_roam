import unittest
import re
import json
import logging
from ankify_roam import roam, anki
from ankify_roam.default_models import ROAM_BASIC, ROAM_CLOZE, add_default_models
from ankify_roam.ankifiers import BlockAnkifier
from ankify_roam.roam import Page, Block, BlockContent
from ankify_roam import util


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
        block.parent = Block.from_string("parent block")
        block.parent.parent = Block.from_string("grandparent block")
        block.parent.parent.parent = Page("Page title")

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

        # All parent blocks and page
        block = Block.from_string("ankified block")
        block.parent = Block.from_string("parent block #ankify-root")
        block.parent.parent = Block.from_string("grandparent block")
        block.parent.parent.parent = Page("Page title")

        ankifier = BlockAnkifier(num_parents="all", tag_ankify_root="ankify-root")
        expected = remove_html_whitespace("""
        <div class="front-side">
            <ul>
                <li class="block parent parent-1 parent-top">parent block <span data-tag="ankify-root" class="rm-page-ref rm-page-ref-tag">#ankify-root</span></li>
                <ul>
                    <li class="block">ankified block</li>
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
            parent=Page("page")
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
            "tags": ["page"]
        }
        self.assertEqual(expected, ankifier.ankify(block))

    def test_ankify_root(self):
        block = Block(
            content=BlockContent.from_string("question"),
            children=[Block.from_string("answer")],
            parent=Page("page")
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
            "tags": ["page"]
        }
        self.assertEqual(expected, ankifier.ankify(block))


def remove_html_whitespace(html_string):
    html_string = re.sub(">\s*\n?\s*<", "><", html_string)
    html_string = re.sub("^\s*\n?\s*", "", html_string)
    html_string = re.sub("\s*\n?\s*$", "", html_string)
    return html_string


if __name__=="__main__":
    unittest.main()