import os
import re
import logging
from functools import reduce
from itertools import zip_longest

logger = logging.getLogger(__name__)

RE_SPLIT_OR = "(?<!\\\)\|"

class BlockContent(list):
    def __init__(self, roam_objects=[]):
        """
        Args:
            roam_objects (List of BlockContentItem)
        """
        for obj in roam_objects:
            self.append(obj)

    @classmethod
    def find_and_replace(cls, string, *args, **kwargs):
        roam_object_types_in_parse_order = [
            CodeBlock,
            Cloze, 
            Image,
            Alias,
            Checkbox,
            View,
            Button,
            PageTag,
            PageRef,
            BlockRef,
            Attribute,
            #Url, #TODO: don't have a good regex for this right now
        ]
        roam_objects = BlockContent([String(string)])
        for rm_obj_type in roam_object_types_in_parse_order:
            roam_objects = rm_obj_type.find_and_replace(roam_objects, *args, **kwargs)
        return cls(roam_objects)

    @classmethod
    def from_string(cls, string, *args, **kwargs):
        return cls.find_and_replace(string, *args, **kwargs)

    def get_tags(self):
        tags = []
        for obj in self:
            tags += obj.get_tags()
        return list(set(tags))

    def to_string(self):
        return "".join([o.to_string() for o in self])

    def to_html(self, *args, **kwargs):
        # TODO: implement filters
        html = "".join([o.to_html(*args, **kwargs) for o in self])
        html = self._markdown_to_html(html)
        return html 

    def is_single_pageref(self):
        return len(self)==1 and type(self[0])==PageRef

    def get_strings(self):
        return [o for o in self if type(o)==String]

    @staticmethod
    def _markdown_to_html(string):
        # TODO: haven't thought much about how this should work
        string = re.sub(r"`([^`]+)`", "<code>\g<1></code>", string)
        string = re.sub(r"\*\*([^\*]+)\*\*", "<b>\g<1></b>", string)
        string = re.sub(r"\_\_([^_]+)\_\_", "<em>\g<1></em>", string)
        string = re.sub(r"\^\^([^\^]+)\^\^", 
            '<span class="roam-highlight">\g<1></span>', string)

        return string

    def __repr__(self):
        return "<%s(%s)>" % (
            self.__class__.__name__, repr(list(self)))


class BlockContentItem:
    @classmethod
    def from_string(cls, string, validate=True):
        if validate and not cls.validate_string(string):
            raise ValueError(f"Invalid string '{string}' for {cls.__name__}")

    @classmethod
    def validate_string(cls, string):
        pat = cls.create_pattern(string)
        pat = "|".join([f"^{p}$" for p in re.split(RE_SPLIT_OR, pat)])
        if re.match(re.compile(pat), string):
            return True
        return False

    @classmethod
    def create_pattern(cls, string):
        "Return regex pattern for sub-strings representing this roam object type"
        raise NotImplementedError

    def to_string(self):
        raise NotImplementedError

    def to_html(self, *args, **kwargs):
        return self.string

    def get_tags(self):
        return []
    
    @classmethod
    def _find_and_replace(cls, string, *args, **kwargs):
        pat = cls.create_pattern(string)
        if not pat:
            return [String(string)]
        "See the find_and_replace method"
        roam_objects = [cls.from_string(s, validate=False, *args, **kwargs) for s in re.findall(pat, string)]
        string_split = [String(s) for s in re.split(pat, string)]
        # Weave strings and roam objects together 
        roam_objects = [a for b in zip_longest(string_split, roam_objects) for a in b if a]
        roam_objects = [o for o in roam_objects if o.to_string()]
        return roam_objects

    @classmethod
    def find_and_replace(cls, string, *args, **kwargs):
        """Replace all substring representations of this object with this object

        Args:
            string (str or sequence of BlockContentItem)

        Returns:
            BlockContent: A sequence of String and this object type. 
        """
        if type(string)==str: 
            roam_objects = BlockContent([String(string)])
        elif type(string)==BlockContent:
            roam_objects = string
        else:
            raise ValueError(f"'{type(string)}' is an invalid type for `string`")

        new_roam_objects = []
        for obj in roam_objects:
            if type(obj)==String:
                new_roam_objects += cls._find_and_replace(obj.to_string(), *args, **kwargs)
            else:
                new_roam_objects += [obj]
        roam_objects = new_roam_objects

        return BlockContent(roam_objects)

    def __repr__(self):
        return "<%s(string='%s')>" % (
            self.__class__.__name__, self.to_string())

    def __eq__(self, b):
        return self.to_string()==b.to_string()


class Cloze(BlockContentItem):
    def __init__(self, id, text, string=None):
        self._id = id
        self.text = text
        self.string = string

    @property
    def id(self):
        return self._id or 1

    @classmethod
    def from_string(cls, string, validate=True, **kwargs):
        super().from_string(string, validate)
        open, text, close = cls.split_string(string)
        m = re.search("\d+", open)
        id = int(m.group()) if m else None
        return cls(id, text, string)

    @classmethod
    def find_and_replace(cls, string, *args, **kwargs):
        roam_objects = super().find_and_replace(string)
        cls._assign_cloze_ids([o for o in roam_objects if type(o)==Cloze])
        return BlockContent(roam_objects)

    @classmethod
    def split_string(cls, string):
        for pat in cls.create_grouped_patterns(string):
            groups = re.findall(pat, string)
            if groups: 
                return groups[0]

    @classmethod
    def create_grouped_patterns(cls, string):
        pat_groups = cls._create_patterns()
        return ["".join([f"({g})" for g in groups]) for groups in pat_groups]

    @classmethod
    def create_pattern(cls, string=None):
        pat_tuples = cls._create_patterns()
        return "|".join(["".join(p) for p in pat_tuples])

    @classmethod
    def _create_patterns(cls, string=None):
        pats = [    
            ("\[\[{c?\d*[:|]?\]\]","[^{}]+","\[\[}\]\]"),
            ("(?<!{){c?\d+[:|]","[^{}]+","}(?!})"),
            ("(?<!{){","[^{}]+","}(?!})")]
        return pats

    def get_tags(self):
        return BlockContent.from_string(self.text).get_tags()

    def to_string(self, style="anki"):
        """
        Args:
            style (string): {'anki','roam'}
        """
        if style=="anki":
            return "{{c%s::%s}}" % (self.id, self.text)
        elif style=="roam":
            return "{c%s:%s}" % (self.id, self.text)
        else:
            raise ValueError(f"style='{style}' is an invalid. "\
                              "Must be 'anki' or 'roam'")

    def to_html(self, *args, **kwargs):
        """
        Args:
            pageref_cloze (str): {'outside', 'inside', 'base_only'}
        """
        proc_cloze = kwargs.get("proc_cloze", True)
        pageref_cloze = kwargs.get("pageref_cloze", "outside")

        if not proc_cloze:
            if self.string:
                sections = self.split_string(self.string)
                htmls = [BlockContent.from_string(s).to_html() for s in sections]
                return "".join(htmls)
            else:
                content = BlockContent.from_string(self.text).to_html()
                return Cloze(self.id, content).to_string()

        roam_objects = BlockContent.from_string(self.text)
        if not roam_objects.is_single_pageref():
            return Cloze(self.id, roam_objects.to_html()).to_string()

        # Fancy options to move around the cloze when it's only around a PageRef
        pageref = roam_objects[0]
        if pageref_cloze=="outside":
            text = pageref.to_html()
            return Cloze(self.id, text).to_string()
        elif pageref_cloze=="inside":
            clozed_title = Cloze(self.id, pageref.title).to_string()
            return pageref.to_html(title=clozed_title)
        elif pageref_cloze=="base_only":
            clozed_base = Cloze(self.id, pageref.get_basename()).to_string()
            namespace = pageref.get_namespace()
            if namespace:
                clozed_base = namespace + "/" + clozed_base
            return pageref.to_html(title=clozed_base)
        else:
            raise ValueError(f"{pageref_cloze} is an invalid option for `pageref_cloze`")
        
    @staticmethod
    def _assign_cloze_ids(clozes):
        assigned_ids = [c._id for c in clozes if c._id]
        next_id = 1
        for cloze in clozes:
            if cloze._id: continue
            while next_id in assigned_ids:
                next_id += 1
            assigned_ids += [next_id]
            cloze._id = next_id

    def __repr__(self):
        return "<%s(id=%s, string='%s')>" % (
            self.__class__.__name__, self._id, self.string)


class Image(BlockContentItem):
    def __init__(self, src, alt="", string=None):
        self.src = src
        self.alt = alt
        self.string = string

    @classmethod
    def from_string(cls, string, validate=True, **kwargs):
        super().from_string(string, validate)
        alt, src = re.search("!\[([^\[\]]*)\]\(([^\)\n]+)\)", string).groups()
        return cls(src, alt)

    @classmethod
    def create_pattern(cls, string=None):
        return r"!\[[^\[\]]*\]\([^\)\n]+\)"

    def to_string(self):
        if self.string: 
            return self.string
        return f"![{self.alt}]({self.src})" 

    def to_html(self, *arg, **kwargs):
        return f'<img src="{self.src}" alt="{self.alt}" draggable="false" class="rm-inline-img">'


class Alias(BlockContentItem):
    def __init__(self, alias, destination, string=None):
        self.alias = alias
        self.destination = destination
        self.string = string

    @classmethod
    def from_string(cls, string, validate=True, **kwargs):
        super().from_string(string, validate)
        alias, destination = re.search(r"^\[([^\[]+)\]\(([\W\w]+)\)$", string).groups()
        if re.match("^\[\[.*\]\]$", destination):
            destination = PageRef.from_string(destination)
        elif re.match("^\(\(.*\)\)$", destination):
            destination = BlockRef.from_string(destination)
        else:
            # TODO: should this be a Url object?
            destination = String(destination)
        return cls(alias, destination, string)

    def to_string(self):
        if self.string:
            return self.string
        return f"[{self.alias}]({self.destination.to_string()})"

    def to_html(self, *arg, **kwargs):
        if type(self.destination)==PageRef:
            return '<a title="page: %s" class="rm-alias rm-alias-page">%s</a>' % (
                self.destination.title, self.alias)
        elif type(self.destination)==BlockRef:
            return '<a title="block: %s" class="rm-alias rm-alias-block">%s</a>' % (
                self.destination.to_string(expand=True), self.alias)
        else:
            return '<a title="url: {0}" class="rm-alias rm-alias-external" href="{0}">{1}</a>'.format(
                self.destination.to_string(), self.alias)

    def get_tags(self):
        return self.destination.get_tags()
    
    @classmethod
    def create_pattern(cls, string=None):
        re_template = r"\[[^\[]+\]\(%s\)"
        destination_pats = []
        for o in [PageRef, BlockRef]:
            dest_pat = o.create_pattern(string)
            destination_pats += re.split(RE_SPLIT_OR, dest_pat) if dest_pat else []
        destination_pats.append("[^\(\)\[\]]+") # TODO: replace this with a real url regex

        return  "|".join([re_template % pat for pat in destination_pats])


class CodeBlock(BlockContentItem):
    def __init__(self, code, language=None, string=None):
        self.code = code
        self.language = language
        self.string = string

    @classmethod
    def from_string(cls, string, **kwargs):
        super().from_string(string)
        supported_languages = ["clojure", "html", "css", "javascript"]
        pat_lang = "^```(%s)\n" % "|".join(supported_languages)
        match_lang = re.search(pat_lang, string)
        if match_lang:
            language = match_lang.group(1)
            pat = re.compile(f"```{language}\n([^`]*)```")
        else:
            language = None
            pat = re.compile("```([^`]*)```")
        code = re.search(pat, string).group(1)
        return cls(code, language, string) 

    @classmethod
    def create_pattern(cls, string=None):
        return f"```[^`]*```"

    def to_string(self):
        if self.string: return self.string 
        if self.language:
            return f'```{self.language}\n{self.code}```'
        else:
            return f'```{self.code}```'

    def to_html(self, *args, **kwargs):
        code = self.code.replace("\n","<br>")
        return f'<pre>{code}</pre>'


class Checkbox(BlockContentItem):
    def __init__(self, checked=False):
        self.checked = checked

    @classmethod
    def from_string(cls, string, validate=True, **kwargs):
        super().from_string(string, validate)
        return cls(checked="DONE" in string)

    @classmethod
    def create_pattern(cls, string=None):
        return re.escape("{{[[TODO]]}}")+"|"+re.escape("{{[[DONE]]}}")

    def get_tags(self):
        return ["DONE"] if self.checked else ["TODO"]

    def to_string(self):
        return "{{[[DONE]]}}" if self.checked else "{{[[TODO]]}}"

    def to_html(self, *arg, **kwargs):
        if self.checked:
            return '<span><label class="check-container"><input type="checkbox" checked=""><span class="checkmark"></span></label></span>'
        else:
            return '<span><label class="check-container"><input type="checkbox"><span class="checkmark"></span></label></span>'


class View(BlockContentItem):
    def __init__(self, name: BlockContentItem, text, string=None):
        if type(name)==str:
            name = String(name)
        self.name = name
        self.text = text
        self.string = string

    @classmethod
    def from_string(cls, string, validate=True, **kwargs):
        super().from_string(string, validate)
        name, text = re.search("{{([^:]*):(.*)}}", string).groups()
        if re.match("^\[\[.*\]\]$", name):
            name = PageRef.from_string(name)
        else:
            name = String(name)
        return cls(name, text, string)

    def to_html(self, *arg, **kwargs):
        return self.text

    def get_tags(self):
        return self.name.get_tags()

    @classmethod
    def create_pattern(cls, strings=None):
        re_template = "{{%s:.*}}"
        pats = []
        for view in ["youtube", "embed", "query", "mentions"]:
            pats.append(re_template % view)
            pats.append(re_template % re.escape(f"[[{view}]]"))
        return "|".join(pats)

    def to_string(self):
        if self.string:
            return self.string
        return "{{%s:%s}}" % (self.name.to_string(), self.text)


class Button(BlockContentItem):
    def __init__(self, name, text="", string=None):
        self.name = name
        self.text = text
        self.string = string

    @classmethod
    def from_string(cls, string, validate=True, **kwargs):
        super().from_string(string, validate)
        contents = string[2:-2]
        if ":" in contents:
            m = re.search(r"(.*):(.*)", contents)
            name, text = m.groups()
        else:
            name, text = contents, ""
        return cls(name, text, string)

    def get_tags(self):
        return BlockContent.from_string(self.text).get_tags()

    def to_string(self):
        if self.string: return self.string
        if self.text:
            return "{{%s:%s}}" % (self.name, self.text)
        else:
            return "{{%s}}" % self.name

    def to_html(self, *arg, **kwargs):
        return '<button class="bp3-button bp3-small dont-focus-block">%s</button>' % self.name

    @classmethod
    def create_pattern(cls, string=None):
        return "{{.(?:(?<!{{).)*}}" 


class PageRef(BlockContentItem):
    def __init__(self, title, uid="", string=None):
        """
        Args:
            title (str or BlockContent)
        """
        if type(title)==str: title = PageRef.find_and_replace(title)
        self._title = title
        self.uid = uid
        self.string = string

    @property
    def title(self):
        return self._title.to_string()

    @classmethod
    def from_string(cls, string, validate=True, **kwargs):
        super().from_string(string, validate)
        roam_objects = PageRef.find_and_replace(string[2:-2])
        return cls(roam_objects, string=string)

    @classmethod
    def create_pattern(cls, string, groups=False):
        page_refs = PageRef.extract_page_ref_strings(string)
        if not page_refs:
            return None
        if groups:
            titles = [re.escape(p[2:-2]) for p in page_refs]
            return "|".join([f"(\[\[)({t})(\]\])" for t in titles])
        else:
            return "|".join([re.escape(p) for p in page_refs])

    def get_tags(self):
        tags_in_title = [o.get_tags() for o in self._title]
        tags_in_title = list(set(reduce(lambda x,y: x+y, tags_in_title)))
        return [self.title] + tags_in_title

    def get_namespace(self):
        return os.path.split(self.title)[0]

    def get_basename(self):
        return os.path.split(self.title)[1]

    def to_string(self):
        if self.string: return self.string
        return f"[[{self.title}]]"

    def to_html(self, title=None, *args, **kwargs):
        if not title: title=self.title
        uid_attr = f' data-link-uid="{self.uid}"' if self.uid else ''
        return \
            f'<span data-link-title="{self.title}"{uid_attr}>'\
            f'<span class="rm-page-ref-brackets">[[</span>'\
            f'<span tabindex="-1" class="rm-page-ref rm-page-ref-link-color">{title}</span>'\
            f'<span class="rm-page-ref-brackets">]]</span>'\
            f'</span>'

    @staticmethod
    def extract_page_ref_strings(string):
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


class PageTag(BlockContentItem):
    def __init__(self, title, string=None):
        """
        Args:
            title (str or BlockContent)
        """
        if type(title)==str: title = PageRef.find_and_replace(title)
        self._title = title
        self.string = string

    @classmethod
    def from_string(cls, string, validate=True, **kwargs):
        super().from_string(string, validate)
        title = re.sub("\[\[([\W\w]*)\]\]", "\g<1>", string[1:])
        roam_objects = PageRef.find_and_replace(title)
        return cls(roam_objects, string)

    @property
    def title(self):
        return self._title.to_string()

    def get_tags(self):
        tags_in_title = [o.get_tags() for o in self._title]
        tags_in_title = list(set(reduce(lambda x,y: x+y, tags_in_title)))
        return [self.title] + tags_in_title

    def to_string(self):
        if self.string:
            return self.string
        return "#"+self.title

    def to_html(self, *arg, **kwargs):
        return f'<span tabindex="-1" data-tag="{self.title}" '\
               f'class="rm-page-ref rm-page-ref-tag">#{self.title}</span>'

    @classmethod
    def create_pattern(cls, string):
        pats = ["#[\w\-_@]+"]
        # Create pattern for page refs which look like tags
        page_ref_pat = PageRef.create_pattern(string)
        if page_ref_pat:
            pats += ["#"+pat for pat in re.split(RE_SPLIT_OR, page_ref_pat)]

        return "|".join(pats)


class BlockRef(BlockContentItem):
    def __init__(self, uid, roam_db=None, string=None):
        self.uid = uid
        self.roam_db = roam_db
        self.string = string

    @classmethod
    def from_string(cls, string, *args, **kwargs):
        super().from_string(string)
        roam_db = kwargs.get("roam_db", None)
        return cls(string[2:-2], roam_db=roam_db, string=string)

    def to_string(self, expand=False):
        if expand:
            block = self.get_referenced_block()
            return block.to_string()
        if self.string:
            return self.string
        else:
            return f"(({self.uid}))"

    def to_html(self, *arg, **kwargs):
        block = self.get_referenced_block()
        text = block.to_html() if block else self.to_string
        return '<div class="rm-block-ref"><span>%s</span></div>' % text

    def get_tags(self):
        return []

    @classmethod
    def create_pattern(cls, string=None):
        return "\(\([\w\d\-_]{9}\)\)"

    def get_referenced_block(self):
        return self.roam_db.get(self.uid)


class Url(BlockContentItem):
    def __init__(self, text):
        self.text = text

    @classmethod
    def from_string(cls, string, **kwargs):
        super().from_string(string)
        return cls(string)

    def to_string(self):
        return self.text

    def to_html(self, *arg, **kwargs):
        return f'<span><a href="{self.text}">{self.text}</a></span>'


class String(BlockContentItem):
    def __init__(self, string):
        self.string = string

    @classmethod
    def from_string(cls, string, validate=True, **kwargs):
        super().from_string(string, validate)
        return cls(string)

    @classmethod
    def validate_string(cls, string):
        return True

    def to_html(self, *arg, **kwargs):
        return self.to_string()

    def get_tags(self):
        return []

    def to_string(self):
        return self.string


class Attribute(BlockContentItem):
    def __init__(self, title, string=None):
        self.title = title
        self.string = string

    @classmethod
    def from_string(cls, string, validate=True, **kwargs):
        super().from_string(string, validate)
        return cls(string[:-2], string)

    @classmethod
    def validate_string(cls, string):
        pat = re.compile(cls.create_pattern(string)+"$")
        if re.match(pat, string):
            return True
        return False

    @classmethod
    def create_pattern(cls, string=None):
        return "^(?:(?<!:)[^:])+::"

    def to_html(self, *arg, **kwargs):
        return '<span><strong tabindex="-1" style="cursor: pointer;">%s:</strong></span>' % self.title

    def get_tags(self):
        return [self.title]

    def to_string(self):
        if self.string:
            return self.string
        return self.title+"::"