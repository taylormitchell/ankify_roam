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
    def __init__(self, deck="Default", note_basic="Roam Basic", note_cloze="Roam Cloze", pageref_cloze="outside", tag_ankify="ankify", tag_dont_ankify="dont-ankify", show_parents=False, max_depth=None):
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
        blocks_to_ankify = roam_graph.query_many(
            lambda b: self.is_block_to_ankify(b),
            include_parents=True)

        logger.info(f"Found {len(blocks_to_ankify)} blocks with ankify tag")

        block_ankifier_args = inspect.getfullargspec(BlockAnkifier.__init__).args
        kwargs = {k:v for k,v in vars(self).items() if k in block_ankifier_args}
        block_ankifier = BlockAnkifier(**kwargs)

        num_added = 0
        num_updated = 0
        num_no_change = 0
        num_failed = 0
        for block in blocks_to_ankify:
            try:
                ankified_note = block_ankifier.ankify(block)
            except:
                logger.exception(f"Failed ankifying {block} during conversion to anki note")
                num_failed += 1
                continue
            try:
                note_id = anki.get_note_id(ankified_note)
                if note_id:
                    existing_fields = {k: v['value'] for k,v in anki.get_note(note_id)['fields'].items()}
                    if existing_fields == ankified_note['fields']:
                        num_no_change += 1
                    else:
                        anki.update_note(ankified_note, note_id)
                        num_updated += 1
                else:
                    anki.add_note(ankified_note)
                    num_added += 1
            except:
                logger.exception(f"Failed ankifying {block} during upload to anki")
                num_failed += 1
        logger.info(f"Results: {num_added} notes added, {num_updated} updated, {num_no_change} unchanged, {num_failed} failed")


class BlockAnkifier:
    def __init__(self, deck="Default", note_basic="Roam Basic", note_cloze="Roam Cloze", pageref_cloze="outside", tag_ankify="ankify", tag_dont_ankify="dont-ankify", show_parents=False, max_depth=None, option_keys=["ankify", "ankify_roam"], field_names={}):
        self.deck = deck
        self.note_basic = note_basic
        self.note_cloze = note_cloze
        self.pageref_cloze = pageref_cloze
        self.tag_ankify = tag_ankify
        self.show_parents = show_parents
        self.max_depth = max_depth
        self.option_keys = option_keys
        self.field_names = field_names 

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

    def _get_option(self, block, option):
        pat = f'''^(\[\[)?({"|".join(self.option_keys)})(\]\])?:\s*{option}\s?=\s?["']?([\w\s]*)["']?$'''
        for tag in block.get_tags():
            m = re.match(pat, tag)
            if m:
                return m.groups()[-1]
        return None

    def _get_note_type(self, block):
        # Search for assigned model
        opt = self._get_option(block, "note")
        if opt:
            return opt
        # Otherwise infer from cloze markup
        if any([type(obj)==roam.Cloze for obj in block.content]):
            return self.note_cloze
        else:
            return self.note_basic

    def _get_deck(self, block):
        opt = self._get_option(block, "deck")
        return opt or self.deck

    def _get_pageref_cloze(self, block):
        opt = self._get_option(block, "pageref-cloze")
        return opt or self.pageref_cloze

    def _get_flashcard_type(self, modelName):
        # Infer from blocks assigned model name 
        if re.search("[Cc]loze", modelName):
            return "cloze"
        else:
            return "basic"

    def _get_show_parents(self, block):
        opt = self._get_option(block, "show-parents")
        if opt:
            if opt=="False":
                return False
            if opt=="True":
                return True
            if re.match("^([1-9]?\d+|0)$", opt):
                return int(opt)
        return self.show_parents

    def _get_max_depth(self, block):
        opt = self._get_option(block, "max-depth")
        if opt:
            if opt=="None":
                return None
            if re.match("^([1-9]?\d+|0)$", opt):
                return int(opt)
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

        # Put into html list
        if len(parents_html) == len(block.parent_blocks)+1: # all parents
            list_html = self._listify_front(parents_html + [question_html], cls='page-title parent')
            return f'<div class="front-side">{list_html}</div>'
        elif len(parents_html) > 0:
            list_html = self._listify_front(parents_html + [question_html])
            return f'<div class="front-side">{list_html}</div>'
        else:
            return f'<div class="front-side">{question_html}</div>'

    def _listify_front(self, block_htmls, cls='block parent'):
        if len(block_htmls)==1:
            return '<ul><li class="block">' + block_htmls[0] + '</li></ul>'
        return f'<ul><li class="{cls}">' + block_htmls[0] + '</li>' + self._listify_front(block_htmls[1:]) + '</ul>'

    def back_to_html(self, block, **kwargs):
        children = block.get("children", [])
        if len(children)>=2:
            return f'<div class="back-side list">{self._listify_back(children, **kwargs)}</div>'
        elif len(children)==1:
            return f'<div class="back-side">{children[0].to_html(**kwargs)}</div>'
        else:
            return '<div class="back-side"></div>'

    def _listify_back(self, blocks, level=0, **kwargs):
        if not blocks:
            return ""
        if self.max_depth is not None and level == self.max_depth:
            return ""
        html_list = "" 
        for block in blocks:
            html_list += f'<li>{block.to_html(**kwargs)}</li>'
            html_list += f'{self._listify_back(block.get("children"), level=level+1)}'
        return f'<ul>{html_list}</ul>'
        