import os
import re
import loaders 
from itertools import zip_longest
import logging

# TODO: should all RoamObjects have self.roam_db? Right now only BlockRef has it
# None of the others need it, but having it is more consistent?
# TODO: I think the extract_*  methods should be in the RoamObject class

RE_ALIAS_TEMPLATE = r"\[[^\[]+\]\(%s\)"
RE_CURLY = "{{.(?:(?<!{{).)*}}" 
RE_TAG = r"#[\w\-_@]+"
RE_PAGE_REF = "\[\[[^\[\]]*\]\]"
RE_BLOCK_REF = "\(\([\w\d\-_]{9}\)\)"


class RoamDb:
    def __init__(self):
        pass

    @classmethod
    def from_json(cls, page_jsons):
        roam_db = cls()
        pages = [Page.from_json(p, roam_db) for p in page_jsons]
        roam_db.add_pages(pages)
        return roam_db

    def add_pages(self, pages):
        self.pages = pages

    def get_tags(self, string):
        RE_PAGE_REF = "\[\[([^\[\]]+)\]\]"
        RE_TAG = "#([\w\d_\-@]+)"
        return list(set(re.findall(RE_PAGE_REF, string)+ re.findall(RE_TAG, string)))

    def get_block_by_uid(self, uid, blocks=None):
        if blocks is None: blocks = self.pages
        for block in blocks:
            if block.get("uid") == uid:
                return block
            block = self.get_block_by_uid(uid, block.get('children',[]))
            if block:
                return block

    def set_tags(self, objs=None, parent_tags=[]):
        if objs is None: objs=self.pages
        for obj in objs:
            if type(obj)==Block:
                obj.set_parent_tags(parent_tags)
            if obj.get("children"):
                self.set_tags(obj.get("children"), parent_tags=obj.get_tags())

    def get_blocks_by_tag(self, tag, objs=None):
        if objs is None: objs=self.pages
        blocks = []
        for obj in objs:
            if tag in obj.get_tags():
                blocks.append(obj)
            blocks += self.get_blocks_by_tag(tag, obj.get("children",[]))
        return blocks

# Roam Containers
# ---------------

class Page:
    def __init__(self, title, children, edit_time, edit_email):
        self.title = title
        self.children = children
        self.edit_time = edit_time
        self.edit_email = edit_email

    def get_tags(self):
        return ['title']

    def get(self, key, default=None):
        return getattr(self, key) if hasattr(self, key) else default

    @classmethod
    def from_json(cls, page, roam_db):
        children = [Block.from_json(c, roam_db) for c in page.get("children",[])]
        return cls(page['title'], children, page['edit-time'], page['edit-email'])

class BlockList(list):
    def __init__(self, blocks=[]):
        for b in blocks:
            self.append(b)

    def _listify(self, blocks, **kwargs):
        if blocks is None:
            return ""
        html = ""
        for block in blocks:
            content = block.to_html(**kwargs) + \
                      self._listify(block.get("children"))
            html += "<li>" + content + "</li>"
        html = "<ul>" + html + "</ul>"
        return html

    def to_html(self, **kwargs):
        if len(self)==0:
            return ""
        elif len(self)==1:
            return self[0].to_html(**kwargs)
        else:
            html = self._listify(self, **kwargs)
            #TODO: should this be a config?
            return '<div class="centered-block">' + html + '</div>'

class Block:
    def __init__(self, string, children: BlockList, uid, create_time, create_email,  edit_time, edit_email, roam_db):
        self.string = string
        self.children = children
        self.uid = uid
        self.create_time = create_time
        self.create_email = create_email
        self.edit_time = edit_time
        self.edit_email = edit_email
        self.roam_db = roam_db
        self.parent_tags = []
        self.objects = []

    def set_parent_tags(self, parent_tags):
        self.parent_tags = parent_tags

    def get(self, key, default=BlockList()):
        return getattr(self, key) if hasattr(self, key) else default

    def get_tags(self):
        return list(set(self.parent_tags + self.get_block_tags()))

    def get_block_tags(self):
        return [tag for obj in self.to_objects() for tag in obj.get_tags()]

    @classmethod
    def from_json(cls, block, roam_db):
        children = BlockList([Block.from_json(c, roam_db) for c in block.get("children",[])])
        return cls(block['string'], children, block['uid'], block.get('create-time'),
                   block.get('create-email'), block.get('edit-time'), block.get('edit-email'), roam_db)

    def to_objects(self, **kwargs):
        string = Cloze.format_clozes(self.string, kwargs.get("uncloze_namespace",False))
        if not self.objects:
            self.objects = self._objectify(self.string)
        return self.objects 

    def to_string(self):
        return "".join([o.to_string() for o in self.to_objects()])

    def to_html(self, **kwargs):
        # TODO: implement filters
        #if "Design Pattern/Composite" in self.string:
        string = "".join([o.to_html() for o in self.to_objects(**kwargs)])
        string = self.markdown_to_html(string)
        string = Cloze.ankify_clozes(string)
        return string 

    def markdown_to_html(self, string):
        # TODO: haven't thought much about how this should work
        string = re.sub(r"`([^`]+)`", "<code>\g<1></code>", string)
        string = re.sub(r"\*\*([^\*]+)\*\*", "<b>\g<1></b>", string)
        string = re.sub(r"\_\_([^_]+)\_\_", "<em>\g<1></em>", string)
        string = re.sub(r"\^\^([^\^]+)\^\^", 
            '<span class="roam-highlight">\g<1></span>', string)

        return string

    def _objectify(self, string):
        roam_objects = [string]
        # NOTE: the order matters!
        for cls in [Alias, Curly, PageRef, PageTag, BlockRef, String]:
            roam_objects = cls.objectify(roam_objects, self.roam_db)

        return roam_objects

    def __repr__(self):
        return "<%s(string='%s')>" % (
            self.__class__.__name__, self.string)

def objectify(string):
    for cls in [Alias, Curly, PageRef, PageTag, BlockRef, String]:
        roam_objects = cls.objectify(roam_objects, self.roam_db)
    return roam_objects


# Roam Objects
# -------------

class Objectifier:
    def __init__(self, string):
        self.string = string

    def _create_patterns(self, string):
        raise NotImplementedError

    @classmethod
    def _objectify(cls, string, pat):
        "See the objectify method"
        objects = [cls(s) for s in re.findall(pat, string)]
        string_split = re.split(pat, string)
        # Weave strings and roam objects together 
        objects = [a for b in zip_longest(string_split, objects) for a in b if a]
        return objects

    @classmethod
    def objectify(cls, objects):
        """Replace all strings representing this object with this object

        Args:
            objects: List of RoamObjects and strings or just a string
        """
        if type(objects)==str: objects = [objects]
        pats = cls._create_patterns(cls, objects)
        for pat in pats:
            new_objects = []
            for obj in objects:
                if type(obj)==str:
                    new_objects += cls._objectify(obj, pat)
                else:
                    new_objects += [obj]
            objects = new_objects

        return objects

class Cloze(Objectifier):
    RE = r"{c?\d*[:|]?[^{}]+}"
    ROAM_TEMPLATE = "{c%s:%s}"
    ANKI_TEMPLATE = "{{c%s::%s}}"

    def __init__(self, string):
        assert self.is_cloze(string)
        super().__init__(string)
        self.id = self._get_id()
        self.content = self._get_content()

    def _get_id(self):
        match = re.search("{c?(\d+)[:|]", self.string)
        if match: 
            return int(match.group(1))

    def _get_content(self):
        return re.sub("{c?\d+[:|]","{", self.string)[1:-1]

    def _create_patterns(self, string):
        return [self.RE] 

    def format(self):
        # TODO: think this would break in the following case: {[[something]] about [[something]]}
        if not self.id: 
            raise ValueError("You need to assign a cloze id before, "\
                             "you can format it")
        match = re.search("^\[\[(.*)\]\]$", self.content)
        if not match:
            return self.ROAM_TEMPLATE % (self.id, self.content)
        # Move clozes surrounding PageRefs inside the PageRef
        return "[[" + self.ROAM_TEMPLATE % (self.id, match.group(1)) + "]]"

    @staticmethod
    def ankify_clozes(string):
        return re.sub("{(c\d+):([^{}]+)}", "{{\g<1>::\g<2>}}", string)

    @staticmethod
    def _assign_cloze_ids(clozes):
        assigned_ids = [id for id in [c.id for c in clozes] if id]
        next_id = 1
        for cloze in clozes:
            if cloze.id: continue
            while next_id in assigned_ids:
                next_id += 1
            assigned_ids += [next_id]
            cloze.id = next_id

    @staticmethod
    def remove_cloze_markup(string):
        return re.sub("{c\d+:([^{}]+)}", "\g<1>", string)

    @classmethod
    def format_clozes(cls, string, uncloze_namespace=False):
        objects = cls.objectify(string)
        cls._assign_cloze_ids([o for o in objects if type(o)==Cloze])

        for i, obj in enumerate(objects):
            if type(obj) != Cloze: continue
            objects[i] = obj.format(uncloze_namespace=uncloze_namespace)

        return "".join(objects)

    @classmethod
    def roam_encloze(cls, id, string):
        return cls.ROAM_TEMPLATE % (id, string)

    @classmethod
    def anki_encloze(cls, id, string):
        return cls.ANKI_TEMPLATE % (id, string)

    @classmethod
    def is_cloze(cls, string):
        return re.search("^"+cls.RE+"$", string) is not None

    def __repr__(self):
        return "<%s(id=%s, string='%s')>" % (
            self.__class__.__name__, self.id, self.string)

# TODO: maybe have two interfaces?:
# class RoamObjInterface
# class RoamObjExtracter
# String wouldn't implement the RoamObjExtractor interface  

class RoamObject:
    def __init__(self, string, roam_db):
        self.string = string
        self.roam_db = roam_db

    def to_string(self):
        return self.string

    def to_html(self):
        raise NotImplementedError

    def get_tags(self):
        raise NotImplementedError

    def _create_patterns(self, roam_objects):
        raise NotImplementedError

    @classmethod
    def _objectify(cls, string, pat, roam_db):
        "See the objectify method"
        roam_objects = [cls(s, roam_db) for s in re.findall(pat, string)]
        string_split = re.split(pat, string)
        # Weave strings and roam objects together 
        roam_objects = [a for b in zip_longest(string_split, roam_objects) for a in b if a]
        return roam_objects

    @classmethod
    def objectify(cls, roam_objects, roam_db):
        """Replace all strings representing this object with this object

        Args:
            roam_objects: List of RoamObjects and strings or just a string
        """
        if type(roam_objects)==str: roam_objects = [roam_objects]
        pats = cls._create_patterns(cls, roam_objects)
        for pat in pats:
            new_roam_objects = []
            for obj in roam_objects:
                if type(obj)==str:
                    new_roam_objects += cls._objectify(obj, pat, roam_db)
                else:
                    new_roam_objects += [obj]
            roam_objects = new_roam_objects

        return roam_objects

    def __repr__(self):
        return "<%s(string='%s')>" % (
            self.__class__.__name__, self.string)

class Alias(RoamObject):
    def __init__(self, string, roam_db):
        super().__init__(string, roam_db)
        pat = "\[(.*)\]\((.*)\)"
        self.alias, ref = re.findall(pat, string.replace("\n"," "))[0]
        if re.match("^\[\[.*\]\]$", ref):
            self.ref = PageRef(ref, roam_db)
        elif re.match("^%s$" % RE_BLOCK_REF, ref):
            self.ref = BlockRef(ref, roam_db)
        else:
            self.ref = URL(ref, roam_db)

    def get_tags(self):
        if type(self.ref)==PageRef:
            return [self.ref.string[2:-2]]
        return []
    
    def to_html(self):
        # TODO: different for block/page/url
        if type(self.ref)==PageRef:
            return '<a title="page: %s">%s</a>' % (self.ref.string, self.alias)
        elif type(self.ref)==BlockRef:
            # TODO: expand block
            return '<a title="block: %s">%s</a>' % (self.ref.string, self.alias)
        else:
            return '<a title="url: %s" hself.ref="%s">%s</a>' % (self.ref.string, self.ref.string, self.alias)

    def _create_patterns(self, roam_objects):
        pats = []
        page_refs = [p for o in roam_objects if type(o)==str 
                       for p in _get_page_ref_strings(o)]
        if page_refs:
            pats.append("|".join([RE_ALIAS_TEMPLATE % re.escape(p) for p in page_refs]))
        pats.append(RE_ALIAS_TEMPLATE % RE_BLOCK_REF)
        pats.append(RE_ALIAS_TEMPLATE % "[^\[\]\(\)]+")

        return pats

class String(RoamObject):
    def __init__(self, string, roam_db):
        super().__init__(string, roam_db)

    def to_html(self):
        return self.string

    def get_tags(self):
        return []

    def _create_patterns(self, roam_objects):
        return [r".*","\n"]

class Curly(RoamObject):
    def __init__(self, string, roam_db):
        super().__init__(string, roam_db)

    def to_html(self):
        return '<button class="bp3-button bp3-small dont-focus-block">%s</button>' % self.string[2:-2]

    def get_tags(self):
        #TODO: these curly can actually have tags in them
        return []

    def _create_patterns(self, roam_objects):
        return [RE_CURLY]


def _get_page_ref_strings(string):
    # https://stackoverflow.com/questions/524548/regular-expression-to-detect-semi-colon-terminated-c-for-while-loops/524624#524624

    bracket_count = 0
    pages = []
    page = ""
    prev_char = ""
    for j,c in enumerate(string):
        # Track page opening and closing
        if prev_char+c == "[[":
            if not page:
                page = string[j-1]
            bracket_count += 1
            prev_char = ""
        elif prev_char+c == "]]":
            bracket_count -= 1
            prev_char = ""
        else:
            prev_char = c
        if page:
            page += c
        # End of page
        if bracket_count == 0 and page:
            pages.append(page)
            page = ""
            
    return pages


class PageRef(RoamObject):
    def __init__(self, string, roam_db):
        super().__init__(string, roam_db)
        try:
            cloze = Cloze(string[2:-2])
        except:
            self.clozed = False
            self.cloze_id = None
            self.content = string[2:-2]
        else:
            self.clozed = True
            self.cloze_id = cloze.id
            self.content = cloze.content

    def get_tags(self):
        # TODO handle case of pages in pages
        return [self.content]

    def get_name(self):
        return self.content

    def get_namespace(self):
        return os.path.split(self.get_name())[0]

    def get_basename(self):
        return os.path.split(self.get_name())[1]

    @staticmethod
    def page_name_to_html(name):
        return \
            f'<span class="rm-page-ref-brackets">[[</span>'\
            f'<span class="rm-page-ref-link-color">{name}</span>'\
            f'<span class="rm-page-ref-brackets">]]</span>'

    def to_html(self, pageref_cloze="outside"):
        """
        Args:
            pageref_cloze (str): {'outside', 'inside', 'base_only'}
        """
        if not self.clozed:
            return self.page_name_to_html(self.get_name())
        if pageref_cloze=="outside":
            page_html = self.page_name_to_html(self.get_name())
            return Cloze.roam_encloze(self.cloze_id, page_html)
        elif pageref_cloze=="inside":
            page_cloze = Cloze.roam_encloze(self.cloze_id, self.get_name())
            return self.page_name_to_html(page_cloze)
        elif pageref_cloze=="base_only":
            clozed_basename = Cloze.roam_encloze(self.cloze_id, self.get_basenamename())
            namespace = self.get_namespace()
            if namespace:
                page_clozed_based = namespace + "/" + clozed_basename
            else:
                page_clozed_based = clozed_basename
            return self.page_name_to_html(page_clozed_based)


    def _create_patterns(self, roam_objects):
        page_names = [p for o in roam_objects if type(o)==str for p in _get_page_ref_strings(o)]
        if page_names:
            pat = "|".join([re.escape(p) for p in page_names])
            return [pat]
        else:
            return []


class PageTag(RoamObject):
    def __init__(self, string, roam_db):
        super().__init__(string, roam_db)

    def _get_name(self):
        # Remove brackets, if any
        string = re.sub("#\[\[(.+)\]\]", '#\g<1>', self.string)
        return string[1:]

    def get_tags(self):
        return [self._get_name()]

    def to_html(self):
        return '<span class="rm-page-ref-tag">#%s</span>' % self._get_name()

    def _create_patterns(self, roam_objects):
        pats = []
        page_names = [p for o in roam_objects if type(o)==str for p in _get_page_ref_strings(o)]
        if page_names:
            pats.append("|".join([re.escape(p) for p in page_names]))
        # The other type of tags
        pats.append(RE_TAG)

        return pats


class BlockRef(RoamObject):
    def __init__(self, string, roam_db):
        super().__init__(string, roam_db)

    def to_html(self):
        uid = self.string[2:-2]
        block = self.roam_db.get_block_by_uid(uid)
        return '<span class="rm-block-ref">%s</span>' % block.to_html()

    def get_tags(self):
        return []

    def _create_patterns(self, roam_objects):
        return [RE_BLOCK_REF]

class URL(RoamObject):
    def __init__(self, string, roam_db):
        super().__init__(string, roam_db)

class Image(RoamObject):
    def __init__(self, string, roam_db):
        super().__init__(string, roam_db)

class CodeBlock(RoamObject):
    def __init__(self, string, roam_db):
        super().__init__(string, roam_db)




if __name__=="__main__":

    # namespace/base code

    # The cloze surrounds a page and the uncloze_namespace flag is on.
    # If the page has a namespace, take it outsself.ide the cloze
    namespace, basename = os.path.split(matches[0])
    clozed_basename = self.ROAM_TEMPLATE % (self.id, basename)
    if namespace: 
        page_name = namespace + "/" + clozed_basename  
    else:
        page_name = clozed_basename


    #string = "something with a {cloze/is/dumb} and {c1:[[this/shoud/work]]} and {2:[[and/this]]} and {3|cloze}"
    #string2 = Block._ankify_clozes(string)
    #print(string2)
    #string2 = Block._ankify_clozes(string, uncloze_namespace=True)
    #print(string2)

    logging.info("Starting")
    pages = loaders.loader("~/Downloads")
    logging.info("Loaded pages")

    roam_db = RoamDb.from_json(pages)
    logging.info("Placed into roam classes")

    #anki_blocks = roam_db.get_blocks_by_tag("anki_note")
    #logging.info("Fetched anki_note blocks")

    block = roam_db.get_block_by_uid("gWD89ydZn")

    import pdb; pdb.set_trace()


    ## All
    #string = "^^this [string](string)^^ {{has}} a [[bit of]] `[[[[every]]thing]] ((wPM3Ha58z)), "\
    #    "[does]` it work? **How about [this]([[THIS]])** or [this]([[[[this]] in this]]) or "\
    #    "[this](((lkjd78-_0))). #[[tags]] #[[at [[the end]]]] #tag_@12"
    #print(string)
    #block = Block(string)
    #print("")
    #print(block.to_objects())
    #print("")
    #print(block.to_html())

    
    # Aliases

    #string = "Some string with a [couple](text) of [aliases]([[page]]) and [blocks](((9485hfgj-))) but not [invalid blocks](((awefaw3)))"
    #print(string)
    #block = Block(string)
    #print(block.extract_aliases([string]))


    # Curly 

    #string = "Some string with {{curly}} brackeys around {{[[different]]}} {{((stuff))}} {{ with { curly inside}}"
    #print(string)
    #block = Block(string)
    #print(block.extract_curlys([string]))


    # Page Referce

    # https://stackoverflow.com/questions/524548/regular-expression-to-detect-semi-colon-terminated-c-for-while-loops/524624#524624
    #string = "this is a string with [[some page [[with this]] inside]] and another [[another page]] derp derp"
    #print(string)
    #block = Block(string)
    #print(block.extract_page_refs([string]))
    #string = "[[some page [[with this]] inside]] [[[[this]][[and this]]]] [[another page]] [[something]"
    #block = Block(string)
    #print(block.extract_page_refs([string]))
     
    
    # Block ref
    #string = "this is a string with ((lkjd78-_0)) but some are invalid ((jalkwef))"
    #print(string)
    #block = Block(string)
    #print(block.extract_block_refs([string]))

    
    #string = "something **with bold**"
    #block = Block(string)
    #print(block.markdown_to_html(string))


    
