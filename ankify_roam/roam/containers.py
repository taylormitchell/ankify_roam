import re
import os
import json
from zipfile import ZipFile
import logging
from ankify_roam.roam.content import *

logger = logging.getLogger(__name__)

class RoamGraph:
    def __init__(self, pages):
        self.pages = [] 
        for page in pages:
            self.pages.append(Page.from_dict(page, self))
        self.propagate_parents()

    @classmethod
    def from_path(cls, path):
        path = os.path.expanduser(path)
        if os.path.isdir(path):
            return cls.from_dir(path)
        elif os.path.splitext(path)[-1]==".zip":
            return cls.from_zip(path)
        elif os.path.splitext(path)[-1]==".json":
            return cls.from_json(path)
        else:
            raise ValueError(f"'{path}' must be refer to a directory, zip, or json")

    @classmethod
    def from_json(cls, path):
        with open(path, encoding='utf-8') as f:
            roam_pages = json.load(f)
        return cls(roam_pages)
    
    @classmethod
    def from_zip(cls, path):
        with ZipFile(path, 'r') as zip_ref:
            filename = zip_ref.namelist()[0]
            if os.path.splitext(filename)[-1]==".md":
                raise ValueError("Roam export must be JSON while the provided is markdown")
            with zip_ref.open(filename) as f:
                roam_pages = json.load(f)
        return cls(roam_pages)

    @classmethod
    def from_dir(cls, path):
        "Initialize using the latest roam export in the given directory"
        roam_exports = [f for f in os.listdir(path) if re.match("Roam-Export-.*", f)]
        if len(roam_exports)==0:
            raise ValueError(f"'{path}' doesn't contain any Roam export zip files")
        filename = sorted(roam_exports)[-1]
        return cls.from_zip(os.path.join(path,filename))

    def get_page(self, title):
        for page in self.pages:
            if page.title==title:
                return page

    def query_many(self, condition):
        blocks = []
        for page in self.pages:
            blocks += page.query_many(condition)
        return blocks

    def query_by_uid(self, uid):
        for page in self.pages:
            block = page.query_by_uid(uid)
            if block:
                return block

    def query_by_tag(self, tag):
        return self.query_many(lambda b: tag in b.get_tags())

    def propagate_parents(self):
        for page in self.pages:
            page.propagate_parents()


class Page:
    def __init__(self, title, children=[], edit_time=None, edit_email=None):
        self.title = title
        self.children = children
        self.edit_time = edit_time
        self.edit_email = edit_email

    def get_attribute(self, key, default=None):
        for o in self.children:
            if o.content and type(o.content[0]) == Attribute and o.content[0].title == key:
                return o.content[1:]
        return default

    def get_tags(self, from_attr=False, drop_duplicates=False, *args, **kwargs):
        tags = [self.title]
        if from_attr:
            bc = self.get_attribute("tags")
            tags += bc.get_tags() if bc else []
        if drop_duplicates:
            tags = list(dict.fromkeys(tags)) # This preserves order
        return tags

    def get(self, key, default=None):
        return getattr(self, key) if hasattr(self, key) else default

    def query_by_uid(self, uid, default=None, blocks=None):
        if blocks is None: blocks = self.get('children',[])
        for block in blocks:
            if block.get("uid") == uid:
                return block
            block = self.query_by_uid(uid, default=default, blocks=block.get('children',[]))
            if block:
                return block
        return default

    def query_many(self, condition, blocks=None):
        if blocks is None: blocks=self.get('children',[])
        res = []
        for block in blocks:
            if condition(block):
                res.append(block)
            res += self.query_many(condition, blocks=block.children)
        return res

    def num_descendants(self):
        count = 0
        for block in self.children:
            count += 1
            count += block.num_descendants()
        return count

    def propagate_parents(self):
        for block in self.children:
            block.propagate_parents(parent=self)

    def to_html(self, *args, **kwargs):
        return PageRef(self.title).to_html(**kwargs)

    @classmethod
    def from_dict(cls, page, roam_db):
        child_block_objects = []
        for block in page.get("children",[]):
            try:
                child_block_objects.append(Block.from_dict(block, roam_db))
            except Exception as e:
                logger.exception(f"Unknown problem parsing block '{block}' :(. Skipping")
        return cls(page['title'], child_block_objects, page.get('edit-time',''), page.get('edit-email',''))


class Block:
    def __init__(self, content=None, children=None, uid="", create_time="", 
                 create_email="",  edit_time="", edit_email="", roam_db=None, 
                 parent=None):
        self.content = content or BlockContent()
        self.children = children or BlockChildren()
        self.uid = uid
        self.create_time = create_time
        self.create_email = create_email
        self.edit_time = edit_time
        self.edit_email = edit_email
        self.roam_db = roam_db
        self.parent_tags = []
        self.objects = []
        self.parent = parent

    @property
    def parents(self):
        if isinstance(self.parent, Page):
            return [self.parent]
        elif isinstance(self.parent, Block):
            return [self.parent] + self.parent.parents
        return []

    @property
    def parent_blocks(self):
        if isinstance(self.parent, Block):
            return [self.parent] + self.parent.parent_blocks
        return []

    @property
    def parent_page(self):
        parent = self.parent
        while parent and not isinstance(parent, Page):
            parent = parent.parent
        return parent

    def get(self, key, default=None):
        if not default: default=BlockChildren()
        return getattr(self, key) if hasattr(self, key) else default

    def get_attribute(self, key, default=None):
        for o in self.children:
            if o.content and type(o.content[0]) == Attribute and o.content[0].title == key:
                return o.content[1:]
        return default

    def get_tags(self, inherit=True, drop_duplicates=False, from_attr=False):
        """Return a list of tags on the block

        The list of tags are ordered such that tags inside the block come first, ordered
        from left to right. If inherit is True, then the tags of it's parent come next, and 
        it's grandparent next, and so on.

        Args:
            inherit: Whether to include parent tags
            drop_duplicates: Drop duplicate tags (keep first)

        Returns:
            list of string: Tags on the block
        """
        tags = self.content.get_tags()
        if inherit:
            if isinstance(self.parent, Page):
                tags += self.parent.get_tags(from_attr=from_attr)
            elif isinstance(self.parent, Block):
                tags += self.parent.get_tags(inherit=True, from_attr=from_attr)
            else:
                pass
        if from_attr:
            # Get tags listed as attribute
            bc = self.get_attribute("tags", [])
            tags += bc.get_tags() if bc else []
        if drop_duplicates:
            tags = list(dict.fromkeys(tags)) # This preserves order
        return tags

    def get_contents(self, recursive=False):
        return self.content.get_contents(recursive=recursive)

    def to_string(self):
        return self.content.to_string()

    #def to_html(self, *args, **kwargs):
    #    return self.content.to_html(*args, **kwargs)

    def to_html(self, children=False, *args, **kwargs):
        if children:
            return self._listify_back([self])
        else:
            return self.content.to_html(*args, **kwargs)

    def _listify_back(self, blocks, **kwargs):
        if not blocks:
            return ""
        html_list = "" 
        for block in blocks:
            html_list += f'<li>{block.to_html(**kwargs)}</li>'
            html_list += f'{self._listify_back(block.get("children"))}'
        return f'<ul>{html_list}</ul>'

    #def _children_to_html(self, block=None, *args, **kwargs):
    #    if not block:
    #        block = self
    #    children = block.get("children")
    #    if not children:
    #        return ""
    #    html_list = "" 
    #    for child in children:
    #        html_list += f'<li>{child.to_html(**kwargs)}</li>'
    #        html_list += f'{self._children_to_html(child)}'
    #    return f'<ul>{html_list}</ul>'

    def num_descendants(self):
        count = 0
        for block in self.children:
            count += 1
            count += block.num_descendants()
        return count

    def propagate_parents(self, parent=None):
        self.parent = parent
        for block in self.children:
            block.propagate_parents(parent=self)

    @classmethod
    def from_dict(cls, block, roam_db=None):
        # TODO: rename this
        content = BlockContent.from_string(block["string"], roam_db=roam_db)
        child_block_objects = []
        for child_block in block.get("children",[]):
            try:
                child_block_objects.append(Block.from_dict(child_block, roam_db))
            except Exception as e:
                logger.error(f"Unknown problem parsing block '{child_block['uid']}' :(. Skipping")
                logger.debug(e, exc_info=1)
        children = BlockChildren(child_block_objects)
        return cls(content, children, block['uid'], block.get('create-time',''),
                   block.get('create-email',''), block.get('edit-time',''), block.get('edit-email',''), 
                   roam_db)

    @classmethod
    def from_string(cls, string, *args, **kwargs):
        content = BlockContent.from_string(string)
        return cls(content, *args, **kwargs)

    def __repr__(self):
        return "<%s(uid='%s', string='%s')>" % (
            self.__class__.__name__, self.uid, self.to_string()[:10]+"...")


class BlockChildren(list):
    def __init__(self, blocks=[]):
        for b in blocks:
            self.append(b)

    def __repr__(self):
        return "<%s(%s)>" % (
            self.__class__.__name__, repr(list(self)))
