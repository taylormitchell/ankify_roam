import argparse
import os
import sys
import logging
import re
import inspect
import string
from itertools import zip_longest
from ankify_roam import roam
from ankify_roam import anki
from ankify_roam.default_models import ROAM_BASIC, ROAM_CLOZE

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

ASCII_NON_PRINTABLE = "".join([chr(i) for i in range(128) 
                               if chr(i) not in string.printable])

class RoamGraphAnkifier:
    def __init__(self, deck="Default", note_basic="Roam Basic", note_cloze="Roam Cloze", pageref_cloze="outside", tag_ankify="ankify", tag_dont_ankify="", show_parents=1, max_depth=None):
        self.deck = deck
        self.note_basic = note_basic
        self.note_cloze = note_cloze
        self.pageref_cloze = pageref_cloze
        self.tag_ankify = tag_ankify
        self.tag_dont_ankify = tag_dont_ankify
        self.show_parents = show_parents
        self.max_depth = max_depth
        
    def check_conn_and_params(self):
        if not anki.connection_open():
            raise ValueError("Couldn't connect to Anki.") 
        if not self.deck in anki.get_deck_names():
            raise ValueError(f"Deck named '{self.deck}' not in Anki.")
        if not self.note_basic in anki.get_model_names():
            raise ValueError(f"Note type named '{self.note_basic}' not in Anki.")
        if not self.note_cloze in anki.get_model_names():
            raise ValueError(f"Note type named '{self.note_cloze}' not in Anki.")
        basic_field_names = anki.get_field_names(self.note_basic)
        if not "uid" in basic_field_names:
            raise ValueError(f"'{self.note_basic}' note type is missing a 'uid' field.")
        if len([fn for fn in basic_field_names[:2] if fn!="uid"]) != 2:
            raise ValueError(f"'{self.note_basic}' note type requires 2 fields (excluding the 'uid' field.)")
        cloze_field_names = anki.get_field_names(self.note_cloze)
        if not "uid" in cloze_field_names:
            raise ValueError(f"'{self.note_cloze}' note type is missing a 'uid' field.")
        if cloze_field_names[0]=="uid":
            raise ValueError(f"'{self.note_cloze}' note type requires 1 field (excluding the 'uid' field.)")
        if not anki.is_model_cloze(self.note_cloze):
            raise ValueError(f"note_cloze must be a cloze note type and '{self.note_cloze}' isn't.")

    def is_block_to_ankify(self, block):
        tags = block.get_tags(inherit=False)
        if self.tag_ankify in tags:
            if self.tag_dont_ankify and self.tag_dont_ankify in tags:
                return False
            return True
        else:
            return False

    def ankify(self, roam_graph):
        self.check_conn_and_params()
        logger.info("Fetching blocks to ankify")
        blocks_to_ankify = roam_graph.query_many(
            lambda b: self.is_block_to_ankify(b),
            include_parents=True)

        logger.info(f"Ankifying {len(blocks_to_ankify)} blocks")

        block_ankifier_args = inspect.getfullargspec(BlockAnkifier.__init__).args
        kwargs = {k:v for k,v in vars(self).items() if k in block_ankifier_args}
        block_ankifier = BlockAnkifier(**kwargs)

        num_added = 0
        num_updated = 0
        for block in blocks_to_ankify:
            try:
                anki_note = block_ankifier.ankify(block)
            except:
                logger.exception(f"Failed ankifying {block} during conversion to anki note")
                continue
            try:
                note_id = anki.get_note_id(anki_note)
                if note_id:
                    anki.update_note(anki_note, note_id)
                    num_updated += 1
                else:
                    anki.add_note(anki_note)
                    num_added += 1
            except:
                logger.exception(f"Failed ankifying {block} during upload to anki")
        logger.info(f"Added {num_added} new notes and updated {num_updated} existing notes")


class BlockAnkifier:
    def __init__(self, deck, note_basic, note_cloze, pageref_cloze, tag_ankify, show_parents, max_depth):
        self.deck = deck
        self.note_basic = note_basic
        self.note_cloze = note_cloze
        self.pageref_cloze = pageref_cloze
        self.tag_ankify = tag_ankify
        self.show_parents = show_parents
        self.max_depth = max_depth
        self.field_names = {}

    def ankify(self, block, **kwargs):
        modelName = self._get_note_type(block)
        deckName = self._get_deck(block)
        if modelName not in self.field_names.keys():
            self.field_names[modelName] = anki.get_field_names(modelName)
        flashcard_type = self._get_flashcard_type(modelName)
        kwargs["pageref_cloze"] = self._get_pageref_cloze(block)
        kwargs["show_parents"] = self._get_show_parents(block)
        kwargs["max_depth"] = self._get_max_depth(block)
        fields = self._block_to_fields(block, self.field_names[modelName], flashcard_type, **kwargs)
        tags = self.ankify_tags(block.get_tags())
        return {
            "deckName": deckName,
            "modelName": modelName,
            "fields": fields,
            "tags": tags
        }

    def ankify_tags(self, roam_tags):
        return [re.sub(r"\s+","_",tag) for tag in roam_tags]

    def _get_note_type(self, block):
        # Search for assigned model
        pat = f'''^(\[\[)?(ankify_roam|ankify)(\]\])?:\s*note=["']?([\w\s]*)["']?$'''
        for tag in block.get_tags():
            m = re.match(pat, tag)
            if m:
                return m.groups()[-1]
        # Otherwise infer from cloze markup
        if any([type(obj)==roam.Cloze for obj in block.content]):
            return self.note_cloze
        else:
            return self.note_basic

    def _get_deck(self, block):
        pat = f'''^(\[\[)?(ankify_roam|ankify)(\]\])?:\s*deck=["']?([\w\s:]+)["']?$'''
        for tag in block.get_tags():
            m = re.match(pat, tag)
            if m:
                return m.groups()[-1]
        return self.deck

    def _get_pageref_cloze(self, block):
        pat = f'''^(\[\[)?(ankify_roam|ankify)(\]\])?:\s*pageref-cloze=["']?(\w+)["']?$'''
        for tag in block.get_tags():
            m = re.match(pat, tag)
            if m:
                return m.groups()[-1]
        return self.pageref_cloze

    def _get_flashcard_type(self, modelName):
        # Infer from blocks assigned model name 
        if re.search("[Cc]loze", modelName):
            return "cloze"
        else:
            return "basic"

    def _get_show_parents(self, block):
        pat = f'''^(\[\[)?(ankify_roam|ankify)(\]\])?:\s*show-parents=["']?(.+)["']?$'''
        for tag in block.get_tags():
            m = re.match(pat, tag)
            if m is None: 
                continue
            value = m.groups()[-1]
            if value=="False":
                return False
            elif value=="True":
                return True
            elif re.match("^([1-9]?\d+|0)$", value):
                return int(value)
            else:
                break
        return self.show_parents

    def _get_max_depth(self, block):
        pat = f'''^(\[\[)?(ankify_roam|ankify)(\]\])?:\s*max-depth=["']?(.+)["']?$'''
        for tag in block.get_tags():
            m = re.match(pat, tag)
            if m is None: 
                continue
            value = m.groups()[-1]
            if value=="None":
                return None
            elif re.match("^([1-9]?\d+|0)$", value):
                return int(value)
            else:
                break
        return self.max_depth

    def _block_to_fields(self, block, field_names, flashcard_type, **kwargs):
        # Convert block content to html
        htmls = []
        if flashcard_type=="cloze":
            htmls.append(self.front_to_html(block, **kwargs))
        else:
            htmls.append(self.front_to_html(block, proc_cloze=False, **kwargs))
            htmls.append(self.back_to_html(block, proc_cloze=False, **kwargs))
        htmls = [re.sub("[%s]" % ASCII_NON_PRINTABLE, "", html) for html in htmls]

        # Assign to content to field names
        fields = {fn: html for fn, html in zip_longest(field_names, htmls, fillvalue="")}
        if "uid" in field_names:
            fields["uid"] = block.uid

        return fields

    def front_to_html(self, block, **kwargs):
        # Convert content to html
        page_title_html = roam.content.PageRef(block.parent_page).to_html(**kwargs)
        parents_kwargs = kwargs.copy()
        parents_kwargs["proc_cloze"] = False # never convert cloze markup in parents to anki clozes
        parent_blocks_html = [p.to_html(**parents_kwargs) for p in block.parent_blocks]
        question_html = block.to_html(**kwargs)
        parents_html = [page_title_html] + parent_blocks_html

        # Keep select number of parent blocks 
        show_parents = kwargs.get("show_parents", self.show_parents)
        if show_parents is True:
            pass 
        elif show_parents is False:
            parents_html = []
        elif type(show_parents)==int:
            parents_html = parents_html[-show_parents:]
        else:
            raise ValueError("Invalid show_parents value")

        # Wrap in div blocks
        if len(parents_html) == len(block.parent_blocks)+1: # all parents
            parents_html[0] = f'<div class="page-title parent">{parents_html[0]}</div>'
            parents_html[1:] = [
                f'<div class="block parent" style="--data-lvl:{i}">{p}</div>'
                for i, p in enumerate(parents_html[1:])]
        else:
            parents_html = [
                f'<div class="block parent" style="--data-lvl:{i}">{p}</div>'
                for i, p in enumerate(parents_html)]
        i = len(parents_html)
        question_html = f'<div class="block" style="--data-lvl:{i}">{question_html}</div>'

        return f'<div class="front-side">%s</div>' % \
               "".join(parents_html+[question_html])

    def back_to_html(self, block, **kwargs):
        children = block.get("children", [])
        if len(children)>=2:
            return '<div class="back-side list">%s</div>' % self._listify(children, **kwargs)
        elif len(children)==1:
            return '<div class="back-side single">%s</div>' % children[0].to_html(**kwargs)
        else:
            return '<div class="back-side"></div>'

    def _listify(self, blocks, level=0, max_depth=None, **kwargs):
        if not blocks:
            return ""
        if max_depth is not None and level == max_depth:
            return ""
        divs = ""
        for block in blocks:
            divs += ''.join([
                f'<div class="block" style="--data-lvl:{level}">',
                    f'<span class="rm-bullet"></span>',
                    f'<div class="rm-block-text">{block.to_html(**kwargs)}</div>'
                f'</div>'
            ])
            divs += self._listify(block.get("children"), level=level+1)
        return divs
        