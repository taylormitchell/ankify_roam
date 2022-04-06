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
    def __init__(self, deck="Default", note_basic="Roam Basic", note_cloze="Roam Cloze", pageref_cloze="outside", tag_ankify="ankify", tag_dont_ankify="dont-ankify", tag_ankify_root="ankify-root", num_parents=0, include_page=False, max_depth=None, tags_from_attr=False):
        self.deck = deck
        self.note_basic = note_basic
        self.note_cloze = note_cloze
        self.pageref_cloze = pageref_cloze
        self.tag_ankify = tag_ankify
        self.tag_dont_ankify = tag_dont_ankify
        self.tag_ankify_root = tag_ankify_root
        self.num_parents = num_parents
        self.include_page = include_page
        self.max_depth = max_depth
        self.tags_from_attr = tags_from_attr
        
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
        tags_in_block = block.get_tags(inherit=False, from_attr=self.tags_from_attr)
        all_tags = block.get_tags(inherit=True, from_attr=self.tags_from_attr)
        if self.tag_ankify in tags_in_block:
            if self.tag_dont_ankify and self.tag_dont_ankify in all_tags:
                return False
            return True
        else:
            return False

    def ankify(self, roam_graph):
        self.check_conn_and_params()
        blocks_to_ankify = roam_graph.query_many(
            lambda b: self.is_block_to_ankify(b))

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
                # Add or update the anki note
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
                # Suspend or unsuspend the anki note
                if ankified_note['suspend'] == True:
                    anki.suspend_note(ankified_note)
                elif ankified_note['suspend'] == False:
                    anki.unsuspend_note(ankified_note)
            except:
                logger.exception(f"Failed ankifying {block} during upload to anki")
                num_failed += 1
        logger.info(f"Results: {num_added} notes added, {num_updated} updated, {num_no_change} unchanged, {num_failed} failed")


class BlockAnkifier:
    def __init__(self, deck="Default", note_basic="Roam Basic", note_cloze="Roam Cloze", pageref_cloze="outside", tag_ankify="ankify", tag_ankify_root="ankify-root", num_parents=0, include_page=False, max_depth=None, option_keys=["ankify", "ankify_roam"], field_names={}, tags_from_attr=False):
        self.deck = deck
        self.note_basic = note_basic
        self.note_cloze = note_cloze
        self.pageref_cloze = pageref_cloze
        self.tag_ankify = tag_ankify
        self.tag_ankify_root = tag_ankify_root
        self.num_parents = num_parents
        self.include_page = include_page
        self.max_depth = max_depth
        self.option_keys = option_keys
        self.field_names = field_names 
        self.tags_from_attr = tags_from_attr

    def ankify(self, block, **kwargs):
        tags = block.get_tags(from_attr=self.tags_from_attr)
        modelName = self._get_note_type(block)
        deckName = self._get_deck(block)
        if modelName not in self.field_names.keys():
            self.field_names[modelName] = anki.get_field_names(modelName)
        flashcard_type = self._get_flashcard_type(modelName)
        kwargs["pageref_cloze"] = self._get_pageref_cloze(block)
        kwargs["num_parents"] = self._get_num_parents(block)
        kwargs["include_page"] = self._get_include_page(block)
        kwargs["max_depth"] = self._get_max_depth(block)
        fields = self._block_to_fields(block, self.field_names[modelName], flashcard_type, **kwargs)
        return {
            "deckName": deckName,
            "modelName": modelName,
            "fields": fields,
            "tags": self.ankify_tags(tags),
            "suspend": self._get_suspend(block)
        }

    def _get_suspend(self, block):
        opt = self._get_option(block, "suspend")
        if opt == 'True':
            return True
        if opt == 'False':
            return False
        return None

    def ankify_tags(self, roam_tags):
        return [re.sub(r"\s+","_",tag) for tag in roam_tags]

    def _get_option(self, block, option):
        pat = f'''^(\[\[)?({"|".join(self.option_keys)})(\]\])?:\s*{option}\s?=\s?(.*)$'''
        for tag in block.get_tags(from_attr=self.tags_from_attr):
            m = re.match(pat, tag)
            if m:
                res = m.groups()[-1]
                # Remove surrounding quotes
                if res.startswith("'") and res.endswith("'"):
                    res = res[1:-1]
                elif res.startswith('"') and res.endswith('"'):
                    res = res[1:-1]
                return res
        return None

    def _get_note_type(self, block):
        # Search for assigned model
        opt = self._get_option(block, "note")
        if opt:
            return opt
        # Otherwise infer from cloze markup
        if any([type(obj)==roam.Cloze for obj in block.get_contents(recursive=True)]):
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

    def _get_num_parents(self, block):
        num_parents = self._get_option(block, "num-parents")
        if num_parents:
            if num_parents == "all":
                return num_parents
            try:
                return int(num_parents)
            except ValueError:
                pass
        return self.num_parents

    def _get_include_page(self, block):
        opt = self._get_option(block, "include-page")
        if opt:
            if opt == 'True':
                return True
            if opt == 'False':
                return False
        return self.include_page

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
            htmls.append(self.front_to_html(block, proc_cloze=True, **kwargs))
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
        parents_kwargs = kwargs.copy()
        parents_kwargs["proc_cloze"] = False # never convert cloze markup in parents to anki clozes
        num_parents_to_include = kwargs.get("num_parents", self.num_parents)
        include_page = kwargs.get("include_page", self.include_page)

        # Get parent blocks up to the root
        parents = block.parents
        if self.tag_ankify_root is not None:
            for i, o in enumerate(parents):
                if self.tag_ankify_root in o.get_tags(inherit=False, from_attr=self.tags_from_attr):
                    break
            parents_to_root = parents[:i+1]

        # Convert content to html
        page_html = block.parent_page.to_html(**parents_kwargs)
        parents_to_root_html = [p.to_html(**parents_kwargs) for p in parents_to_root]
        question_html = block.to_html(**kwargs)

        # Select parents to include 
        if num_parents_to_include == "all":
            num_parents_to_include = len(parents_to_root)
        else:
            num_parents_to_include = min(num_parents_to_include, len(parents_to_root))
        parents_selected_html = parents_to_root_html[:num_parents_to_include]
        # Add page to selection
        if include_page: 
            if len(parents_selected_html) == len(parents):  # Page is already included
                pass
            elif len(parents_selected_html) == len(parents) - 1:  # Selected parents is only missing the top page
                parents_selected_html = parents_selected_html + [page_html]
            else:
                parents_selected_html = parents_selected_html + ['<span class="ellipsis">...</span>'] + [page_html]
            

        # Put into html list
        if len(parents_selected_html) == len(parents): # all parents
            list_html = self._listify_front(parents_selected_html[::-1] + [question_html], cls='page-title')
            return f'<div class="front-side">{list_html}</div>'
        elif len(parents_selected_html) > 0:
            list_html = self._listify_front(parents_selected_html[::-1] + [question_html])
            return f'<div class="front-side">{list_html}</div>'
        else:
            return f'<div class="front-side">{question_html}</div>'

    def _listify_front(self, block_htmls, cls='block', depth=0):
        if len(block_htmls)==1:
            return '<ul><li class="block">' + block_htmls[0] + '</li></ul>'
        cls += f" parent parent-{len(block_htmls)-1}"
        if depth == 0: cls += " parent-top"
        return f'<ul><li class="{cls}">' + block_htmls[0] + '</li>' + \
            self._listify_front(block_htmls[1:], 'block', depth+1) + '</ul>'
        

    def back_to_html(self, block, **kwargs):
        children = block.get("children", [])
        num_descendants = block.num_descendants()
        if num_descendants >= 2:
            return f'<div class="back-side list">{self._listify_back(children, **kwargs)}</div>'
        elif num_descendants == 1:
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
        