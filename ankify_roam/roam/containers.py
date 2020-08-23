import re
import os
import json
from zipfile import ZipFile
import logging
from ankify_roam.roam.content import *

logger = logging.getLogger(__name__)

class RoamGraph:
    def __init__(self, pages):
        self.pages = [Page.from_dict(p, self) for p in pages]
        self.apply_tag_inheritance()

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
        with open(path) as f:
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

    def query_many(self, condition, include_parents=True):
        blocks = []
        for page in self.pages:
            blocks += page.query_many(condition, include_parents=include_parents)
        return blocks

    def query_by_uid(self, uid, include_parents=True):
        for page in self.pages:
            block = page.query_by_uid(uid, include_parents=include_parents)
            if block:
                return block

    def query_by_tag(self, tag, include_parents=True):
        return query_many(lambda b: tag in b.get_tags())

    def _apply_tag_inheritance(self, blocks, parent_tags=[]):
        for block in blocks:
            if type(block)==Block:
                block.set_parent_tags(parent_tags)
            if block.get("children"):
                self._apply_tag_inheritance(block.get("children"), parent_tags=block.get_tags())

    def apply_tag_inheritance(self):
        for page in self.pages:
            self._apply_tag_inheritance(page.get("children",[]), parent_tags=page.get_tags())


class Page:
    def __init__(self, title, children, edit_time, edit_email):
        self.title = title
        self.children = children
        self.edit_time = edit_time
        self.edit_email = edit_email

    def get_tags(self):
        return [self.title]

    def get(self, key, default=None):
        return getattr(self, key) if hasattr(self, key) else default

    def query_by_uid(self, uid, default=None, blocks=None, parent_blocks=[], include_parents=True):
        if blocks is None: blocks = self.get('children',[])
        for block in blocks:
            if block.get("uid") == uid:
                if include_parents: 
                    block.parent_page = self.title
                    block.parent_blocks = parent_blocks
                return block
            block = self.query_by_uid(uid, default=default, blocks=block.get('children',[]),
                parent_blocks=parent_blocks+[block.content])
            if block:
                return block
        return default

    def query_many(self, condition, blocks=None, parent_blocks=[], include_parents=True):
        if blocks is None: blocks=self.get('children',[])
        res = []
        for block in blocks:
            if condition(block):
                if include_parents: 
                    block.parent_page = self.title
                    block.parent_blocks = parent_blocks
                res.append(block)
            res += self.query_many(
                condition, 
                include_parents=include_parents,
                blocks=block.children, 
                parent_blocks=parent_blocks+[block.content] if include_parents else None)
        return res

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
                 parent_blocks=None, parent_page=None):
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
        self.parent_blocks = parent_blocks
        self.parent_page = parent_page

    def set_parent_tags(self, parent_tags):
        self.parent_tags = parent_tags

    def get(self, key, default=None):
        if not default: default=BlockChildren()
        return getattr(self, key) if hasattr(self, key) else default

    def get_tags(self, inherit=True):
        if inherit:
            return list(set(self.parent_tags + self.content.get_tags()))
        else:
            return list(set(self.content.get_tags()))

    def to_string(self):
        return self.content.to_string()

    def to_html(self, *args, **kwargs):
        return self.content.to_html(*args, **kwargs)

    @classmethod
    def from_dict(cls, block, roam_db):
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
                   block.get('create-email',''), block.get('edit-time',''), block.get('edit-email',''), roam_db)

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

