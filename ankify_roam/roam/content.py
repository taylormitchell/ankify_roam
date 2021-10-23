import os
import re
import logging
from functools import reduce
from itertools import zip_longest
from collections.abc import Iterable
import html

logger = logging.getLogger(__name__)

RE_SPLIT_OR = "(?<!\\\)\|"



class BlockContent(list):
    def __init__(self, roam_objects=[]):
        """
        Args:
            roam_objects (List of BlockContentItem)
        """
        if type(roam_objects) not in [list, BlockContent]:
            roam_objects = [roam_objects]
        for obj in roam_objects:
            if type(obj) in [str, int, float]:
                obj = String(str(obj))
            elif isinstance(obj, BlockContentItem):
                pass
            else:
                raise ValueError(f"roam_objects can't contain {type(obj)} type objects")
            self.append(obj)

    @classmethod
    def find_and_replace(cls, obj, skip=[], *args, **kwargs):
        roam_object_types = [
            BlockQuote,
            CodeBlock,
            CodeInline,
            Cloze, 
            Image,
            Alias,
            Checkbox,
            Embed,
            View,
            Button,
            PageTag,
            PageRef,
            BlockRef,
            Attribute,
            #Url, #TODO: don't have a good regex for this right now
        ]
        roam_object_types = [o for o in roam_object_types if o not in skip]
        roam_objects = BlockContent(obj)
        for rm_obj_type in roam_object_types:
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
        res = "".join([o.to_html(*args, **kwargs) for o in self])
        res = self._all_emphasis_to_html(res)
        return res 

    def is_single_pageref(self):
        return len(self)==1 and type(self[0])==PageRef

    def get_strings(self):
        return [o for o in self if type(o)==String]

    @staticmethod
    def _get_emphasis_locs(string, emphasis):
        emphasis_locs = []
        emphasis_start = emphasis_end = None 
        for i,c in enumerate(string):
            if emphasis_start is None and string[i:i+len(emphasis)] == emphasis:
                emphasis_start = i
                continue
            if emphasis_end is None and string[i:i+len(emphasis)] == emphasis:
                emphasis_end = i + (len(emphasis)-1)
                emphasis_locs.append((emphasis_start, emphasis_end))
                emphasis_start = emphasis_end = None

        return emphasis_locs

    def _emphasis_to_html(self, string, emphasis, html_left, html_right):
        emphasis_locs = self._get_emphasis_locs(string, emphasis)
        diff = 0
        for (i, j) in emphasis_locs:
            i, j = i + diff, j + diff
            string = string[:i] + html_left + string[i+len(emphasis):j-len(emphasis)+1] + html_right + string[j+1:]
            diff += len(html_left+html_right) - len(emphasis+emphasis)
        return string

    def _all_emphasis_to_html(self, string):
        string = self._emphasis_to_html(string, emphasis="`", html_left="<code>", html_right="</code>")
        string = self._emphasis_to_html(string, emphasis="**", html_left="<b>", html_right="</b>")
        string = self._emphasis_to_html(string, emphasis="__", html_left="<em>", html_right="</em>")
        string = self._emphasis_to_html(string, emphasis="^^", html_left='<span class="roam-highlight">', html_right='</span>')
        return string

    def __repr__(self):
        return "<%s(%s)>" % (
            self.__class__.__name__, repr(list(self)))

    def get_contents(self, recursive=False):
        if not recursive:
            return list(self)
        else:
            items = []
            for item in self:
                items += [item]
                items += item.get_contents()
            return items

    def merge_adjacent_strings(self):
        i = 0
        while i + 1 < len(self):
            if type(self[i]) == String and type(self[i+1]) == String:
                self[i].string += self[i+1].string
                del self[i+1]
            else:
                i += 1


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

    def to_string(self):
        raise NotImplementedError

    def to_html(self, *args, **kwargs):
        return self.string

    def get_tags(self):
        return []

    def get_contents(self):
        return []
    
    @classmethod
    def _find_and_replace(cls, string, *args, **kwargs):
        "See the find_and_replace method"
        pat = cls.create_pattern(string)
        if not pat:
            return [String(string)]
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


class BlockQuote(BlockContentItem):
    def __init__(self, block_content, prefix="> "):
        self.block_content = block_content
        self.prefix = prefix

    @classmethod
    def from_string(cls, string, validate=True, **kwargs):
        super().from_string(string, validate)
        prefix, quote = re.match("^(>\s?)([\w\W]*)$", string).groups()
        block_content = BlockContent.from_string(quote, **kwargs)
        return cls(block_content, prefix=prefix)

    def to_string(self):
        return self.prefix + self.block_content.to_string()

    def to_html(self, *args, **kwargs):
        return '<blockquote class="rm-bq">' + self.block_content.to_html(*args, **kwargs) + '</blockquote>'

    def get_tags(self):
        return self.block_content.get_tags()

    def get_contents(self):
        return self.block_content.get_contents()
    
    @classmethod
    def create_pattern(cls, string=None):
        return "^>[\w\W]*$"

    def __eq__(self, other):
        return type(self)==type(other) and self.block_content.to_string()==other.block_content.to_string() 


class ClozeLeftBracket(BlockContentItem):
    """
    - {
    - {1
    - {1:
    - {c1:
    - [[{c1:]]
    """
    def __init__(self, id=None, enclosed=False, c=False, sep=""):
        self.id = id 
        self.enclosed = enclosed
        self.c = c
        self.sep = sep

    @classmethod
    def _find_and_replace(cls, string):
        pats = [ 
            "\[\[{c?\d*[:|]?\]\]", # [[{]] or [[{c1:}]]
            "(?<!{){c?\d+[:|]", # {1 or {c1:
            "(?<!{){(?!{)" # {
        ]
        matches = list(re.finditer("|".join(pats), string))
        if not matches:
            return [String(string)]
        objs = []
        last_cloze_end = 0
        for match in matches:
            # Create cloze
            text = match.group(0)
            c = "c" in text
            enclosed = text.startswith("[[")
            m = re.search("\d+", text)
            id = int(m.group(0)) if m else None
            if ":" in text:
                sep = ":"
            elif "|" in text:
                sep = "|"
            else:
                sep = ""
            # Split string and replace with objects
            objs.append(String(string[last_cloze_end:match.start()]))
            objs.append(cls(id, enclosed, c, sep))
            last_cloze_end = match.end()
        if last_cloze_end != len(string):
            objs.append(String(string[last_cloze_end:]))
        return BlockContent(objs)
    
    def to_string(self):
        res = "{"
        if self.c: 
            res += "c"
        if self.id:
            res += str(self.id)
        if self.sep:
            res += self.sep
        if self.enclosed:
            res = "[[" + res + "]]"
        return res

    def to_html(self):
        return "{{c" + str(self.id) + "::"

    def __repr__(self):
        return "<%s(string='%s')>" % (
            self.__class__.__name__, self.to_string())


class ClozeRightBracket(BlockContentItem):
    """
    - [[::hint}]]
    - [[}]]
    - [[::hint]]}
    - }
    - ::hint}
    """
    def __init__(self, enclosed=False, hint=None, string=None):
        self.enclosed = enclosed
        self.hint = hint
        self.string = string

    @classmethod
    def _find_and_replace(cls, string):
        pats = [ 
            "\[\[(?:::[^}\[]*)?}\]\]", # [[}]] or [[::hint}]] 
            "\[\[(?:::[^}\[]*)\]\]}", # [[::hint]]}
            "(?:::[^}\[]*)}(?!})", # ::hint}
            "(?<!})}(?!})", # }
        ]
        matches = re.finditer("|".join(pats), string)
        if not matches:
            return [String(string)]
        objs = []
        last_cloze_end = 0
        for match in matches:
            text = match.group(0)
            # [[}]] or [[::hint}]] 
            if text.startswith("[[") and text.endswith("]]"):
                hint = ClozeHint(re.sub("[\[\]}]", "", text)[2:]) if "::" in text else None
                enclosed = True
            # [[::hint]]}
            elif text.startswith("[[") and text.endswith("}"):
                hint = ClozeHint(re.sub("[\[\]}]", "", text)[2:], enclosed=True)
                enclosed = False
            # } or ::hint}
            else:
                hint = ClozeHint(re.sub("[\[\]}]", "", text)[2:]) if "::" in text else None
                enclosed = False
            # Split string and replace with objects
            objs.append(String(string[last_cloze_end:match.start()]))
            objs.append(cls(enclosed, hint=hint))
            last_cloze_end = match.end()
        if last_cloze_end != len(string):
            objs.append(String(string[last_cloze_end:]))
        return BlockContent(objs)
        
    def to_string(self):
        res = "}"
        if self.hint:
            res = self.hint.to_string() + res
        if self.enclosed:
            res = "[[" + res + "]]"
        return res

    def to_html(self):
        if self.hint:
            return self.hint.to_html() + "}}"
        return "}}"

    def __repr__(self):
        return "<%s(string='%s')>" % (
            self.__class__.__name__, self.to_string())


class ClozeHint(BlockContentItem):
    """
    - {something::hint}
    - {something[[::hint]]}
    - [[{]]something::hint[[}]]
    - [[{]]something[[::hint}]]
    """
    def __init__(self, text, enclosed=False):
        self.text = text
        self.enclosed = enclosed

    @classmethod
    def from_string(cls, hint):
        return cls(hint[2:]) 

    @classmethod
    def _find_and_replace(cls, string):
        pats = [
            "\[\[::[^\]]*\]\]",
            "::[^}\[]*"
        ]
        matches = re.finditer("|".join(pats), string)
        if not matches:
            return BlockContent(string)
        objs = []
        last_cloze_end = 0
        for match in matches:
            text = match.group(0)
            if text.startswith("[["):
                enclosed = True
                text = text[2:-2] # remove surround brackets
            else:
                enclosed = False 
            text = text[2:] # remove '::' prefix 
            objs.append(String(string[last_cloze_end:match.start()]))
            objs.append(cls(text, enclosed))
            last_cloze_end = match.end()
        if last_cloze_end != len(string):
            objs.append(String(string[last_cloze_end:]))
        return BlockContent(objs)

    def to_string(self):
        res = "::" + str(self.text)
        if self.enclosed:
            res = "[[" + res + "]]"
        return res

    def to_html(self):
        return "::" + str(self.text)


class Cloze(BlockContentItem):
    def __init__(self, inner:BlockContent="", left_bracket:ClozeLeftBracket=None, right_bracket:ClozeRightBracket=None, 
                 hint:ClozeHint=None, id=1, c=True, sep=":", enclosed=False, string=None, roam_db=None):
        self.inner = BlockContent(inner)
        self.left_bracket = left_bracket or ClozeLeftBracket(id=id, c=c, enclosed=enclosed, sep=sep)
        self.right_bracket = right_bracket or ClozeRightBracket(enclosed=enclosed)
        if self.right_bracket.hint and hint:
            raise ValueError("Only allowed one hint")
        if type(hint) == str:
            hint = ClozeHint(hint)
        self._hint = hint
        self.string = string
        self.roam_db = roam_db

    @property
    def hint(self):
        return self._hint or self.right_bracket.hint
    
    @property
    def id(self):
        return self.left_bracket.id if self.left_bracket else None

    @id.setter
    def id(self, id):
        self.left_bracket.id = id

    @classmethod
    def from_string(cls, string, validate=True, **kwargs):
        objs = cls.find_and_replace(string)
        if len(objs) != 1 or type(objs[0]) != cls:
            raise ValueError(f"Invalid string '{string}' for {cls.__name__}")
        return objs[0]

    @classmethod
    def find_and_replace(cls, string, *args, **kwargs):
        objs = BlockContent(string)
        objs = ClozeLeftBracket.find_and_replace(objs)
        objs = ClozeRightBracket.find_and_replace(objs)
        objs = ClozeHint.find_and_replace(objs)

        res = []
        next_idx = 0
        left_idx = right_idx = None
        for i, obj in enumerate(objs):

            # Left cloze bracket 
            if right_idx is None and type(obj) == ClozeLeftBracket: 
                res += objs[next_idx:i]
                next_idx = left_idx = i

            # Right cloze bracket matched to previous left bracket
            elif left_idx is not None and type(obj) == ClozeRightBracket:
                inner = objs[left_idx+1:i]
                hint = None
                if type(inner[-1]) == ClozeHint:
                    inner, hint = inner[:-1], inner[-1]
                inner = BlockContent.find_and_replace(inner)
                cloze = cls(inner=inner, left_bracket=objs[left_idx], right_bracket=obj, hint=hint)
                res.append(cloze)
                left_idx = right_idx = None
                next_idx = i+1
            
            # Left bracket after an unmatched left bracket
            elif left_idx is not None and type(obj) == ClozeLeftBracket:
                res += objs[left_idx:i]
                next_idx = left_idx = i
            
            # Right bracket after an unmatched right bracket
            elif right_idx is not None and type(obj) == ClozeRightBracket:
                res += objs[right_idx:i]
                next_idx = right_idx = i
        res += objs[next_idx:]

        # Remove any cloze brackets or hints which weren't matched up
        for i, obj in enumerate(res):
            if type(obj) in [ClozeLeftBracket, ClozeRightBracket, ClozeHint]:
                res[i] = String(obj.to_string())

        cls._assign_cloze_ids([o for o in res if type(o)==Cloze])

        bc = BlockContent(res)
        bc.merge_adjacent_strings()

        return bc 

    def get_tags(self):
        return self.inner.get_tags()

    def to_string(self, style="anki"):
        """
        Args:
            style (string): {'anki','roam'}
        """
        if style=="anki":
            return "{{c%s::%s%s}}" % (self.id, self.inner.to_string(), self.hint.to_string() if self.hint else "")
        elif style=="roam":
            res = ""
            for o in [self.left_bracket, self.inner, self._hint, self.right_bracket]:
                res += o.to_string() if o else ""
            return res
        else:
            raise ValueError(f"style='{style}' is an invalid. "\
                              "Must be 'anki' or 'roam'")

    def to_html(self, *args, **kwargs):
        """
        Args:
            pageref_cloze (str): {'outside', 'inside', 'base_only'}
        """
        kwargs['roam_db'] = self.roam_db
        proc_cloze = kwargs.get("proc_cloze", True)
        pageref_cloze = kwargs.get("pageref_cloze", "outside")

        if not proc_cloze:
            bc = BlockContent.find_and_replace(self.to_string("roam"), skip=[Cloze])
            return bc.to_html(*args, **kwargs)

        # Fancy options to move around the cloze when it's only around a PageRef
        if self.inner.is_single_pageref() and self.hint is None:
            pageref = self.inner[0]
            if pageref_cloze=="outside":
                content = pageref.to_html()
                return Cloze(id=self.id, inner=content, hint=self.hint).to_string()
            elif pageref_cloze=="inside":
                clozed_title = Cloze(id=self.id, inner=pageref.title, hint=self.hint).to_string()
                return pageref.to_html(title=clozed_title)
            elif pageref_cloze=="base_only":
                clozed_base = Cloze(id=self.id, inner=pageref.get_basename(), hint=self.hint).to_string()
                namespace = pageref.get_namespace()
                if namespace:
                    clozed_base = namespace + "/" + clozed_base
                return pageref.to_html(title=clozed_base)
            else:
                raise ValueError(f"{pageref_cloze} is an invalid option for `pageref_cloze`")
            
        res = ""
        for o in [self.left_bracket, self.inner, self._hint, self.right_bracket]:
            res += o.to_html() if o else ""
        return res
        
    @staticmethod
    def _assign_cloze_ids(clozes):
        assigned_ids = [c.id for c in clozes if c.id]
        next_id = 1
        for cloze in clozes:
            if cloze.id: continue
            while next_id in assigned_ids:
                next_id += 1
            assigned_ids += [next_id]
            cloze.id = next_id

    def __repr__(self):
        string = self.string or self.to_string(style="roam")
        return "<%s(id=%s, string='%s')>" % (
            self.__class__.__name__, self.id, string)

    def __eq__(self, other):
        return type(self)==type(other) and self.inner == other.inner


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
        return f'<img src="{html.escape(self.src)}" alt="{html.escape(self.alt)}" draggable="false" class="rm-inline-img">'

    def __eq__(self, other):
        return type(self)==type(other) and self.src==other.src and self.alt==other.alt


class Alias(BlockContentItem):
    def __init__(self, alias, destination, string=None):
        self.alias = alias
        self.destination = destination
        self.string = string

    @classmethod
    def from_string(cls, string, validate=True, **kwargs):
        super().from_string(string, validate)
        alias, destination = re.search(r"^\[([^\[\]]+)\]\(([\W\w]+)\)$", string).groups()
        if re.match("^\[\[.*\]\]$", destination):
            destination = PageRef.from_string(destination)
        elif re.match("^\(\(.*\)\)$", destination):
            roam_db = kwargs.get("roam_db", None)
            destination = BlockRef.from_string(destination, roam_db=roam_db)
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
                html.escape(self.destination.title), html.escape(self.alias))
        elif type(self.destination)==BlockRef:
            return '<a title="block: %s" class="rm-alias rm-alias-block">%s</a>' % (
                html.escape(self.destination.to_string(expand=True)), html.escape(self.alias))
        else:
            return '<a title="url: {0}" class="rm-alias rm-alias-external" href="{0}">{1}</a>'.format(
                html.escape(self.destination.to_string()), html.escape(self.alias))

    def get_tags(self):
        return self.destination.get_tags()

    def get_contents(self):
        return self.destination.get_contents()
    
    @classmethod
    def create_pattern(cls, string=None):
        re_template = r"\[[^\[\]]+\]\(%s\)"
        destination_pats = []
        for o in [PageRef, BlockRef]:
            dest_pat = o.create_pattern(string)
            destination_pats += re.split(RE_SPLIT_OR, dest_pat) if dest_pat else []
        destination_pats.append("[^\(\)\[\]]+") # TODO: replace this with a real url regex

        return  "|".join([re_template % pat for pat in destination_pats])

    def __eq__(self, other):
        return type(self)==type(other) and self.alias==other.alias and other.destination==other.destination


class CodeBlock(BlockContentItem):
    def __init__(self, code, language=None, string=None):
        self.code = code
        self.language = language
        self.string = string

    @classmethod
    def from_string(cls, string, **kwargs):
        #super().from_string(string)
        #supported_languages = [
        #    "clojure", "css", "elixir", "html", "plain text", "python", "ruby", 
        #    "swift", "typescript", "isx", "yaml", "rust", "shell", "php", "java", 
        #    "c#", "c++", "objective-c", "kotlin", "sql", "haskell", "scala", 
        #    "common lisp", "julia", "sparql", "turtle", "javascript"]
        #pat_lang = "^```(%s)\n" % "|".join([re.escape(l) for l in supported_languages])
        #match_lang = re.search(pat_lang, string)
        #if match_lang:
        #    language = match_lang.group(1)
        #    pat = re.compile(f"```{language}\n([^`]*)```")
        #else:
        #    language = None
        #    pat = re.compile("```([^`]*)```")
        #code = re.search(pat, string).group(1)
        #return cls(code, language, string) 
        objs = cls.find_and_replace(string)
        if len(objs) != 1 or type(objs[0]) != cls:
            raise ValueError(f"Invalid string '{string}' for {cls.__name__}")
        return objs[0]

    @classmethod
    def _find_and_replace(cls, string):
        supported_languages = [
            "clojure", "css", "elixir", "html", "plain text", "python", "ruby", 
            "swift", "typescript", "isx", "yaml", "rust", "shell", "php", "java", 
            "c#", "c++", "objective-c", "kotlin", "sql", "haskell", "scala", 
            "common lisp", "julia", "sparql", "turtle", "javascript"]
        code_bookends = list(re.finditer("```", string))
        content = []
        string_start = 0
        while len(code_bookends) > 1:
            code_start, code_end = code_bookends.pop(0), code_bookends.pop(0)
            code_block = string[code_start.start():code_end.end()]
            code = string[code_start.end():code_end.start()]
            try:
                first_line = re.search("^.*\n", code).group().strip()
                language = first_line if first_line in supported_languages else None
            except AttributeError:
                language = None
            content.append(String(string[string_start:code_start.start()]))
            content.append(CodeBlock(code, language, code_block))
            string_start = code_end.end()
        content.append(String(string[string_start:]))

        return BlockContent([c for c in content if c.to_string()])

    #@classmethod
    #def create_pattern(cls, string=None):
    #    return f"```[^`]*```"

    def to_string(self):
        if self.string: return self.string 
        if self.language:
            return f'```{self.language}\n{self.code}```'
        else:
            return f'```{self.code}```'

    def to_html(self, *args, **kwargs):
        code = html.escape(self.code)
        return f'<pre><code>{code}</code></pre>'

    def __eq__(self, other):
        return type(self)==type(other) and self.language==other.language and self.code==other.code


class CodeInline(BlockContentItem):
    def __init__(self, code, string=None):
        self.code = code
        self.string = string

    @classmethod
    def from_string(cls, string, **kwargs):
        super().from_string(string)
        pat = re.compile("`([^`]*)`")
        code = re.search(pat, string).group(1)
        return cls(code, string) 

    @classmethod
    def create_pattern(cls, string=None):
        return "`[^`]*`"

    def to_string(self):
        if self.string: return self.string 
        return f'`{self.code}`'

    def to_html(self, *args, **kwargs):
        code = html.escape(self.code)
        return f'<code>{code}</code>'

    def __eq__(self, other):
        return type(self)==type(other) and self.code==other.code


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

    def __eq__(self, other):
        return type(self)==type(other) and self.checked==other.checked


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
        return html.escape(self.text)

    def get_tags(self):
        return self.name.get_tags()

    def get_contents(self):
        return self.name.get_contents()

    @classmethod
    def create_pattern(cls, strings=None):
        re_template = "{{%s:.*}}"
        pats = []
        for view in ["youtube", "query", "mentions"]:
            pats.append(re_template % view)
            pats.append(re_template % re.escape(f"[[{view}]]"))
        return "|".join(pats)

    def to_string(self):
        if self.string:
            return self.string
        return "{{%s:%s}}" % (self.name.to_string(), self.text)

    def __eq__(self, other):
        return type(self)==type(other) and self.name==other.name and self.text==other.text


class Embed(BlockContentItem):
    def __init__(self, name: BlockContentItem, blockref, string=None):
        if type(name)==str:
            name = String(name)
        self.name = name
        self.blockref = blockref
        self.string = string

    @classmethod
    def from_string(cls, string, validate=True, **kwargs):
        super().from_string(string, validate)
        name, blockref = re.search("{{([^:]*):\s*([^\s]*)\s*}}", string).groups()
        if re.match("^\[\[.*\]\]$", name):
            name = PageRef.from_string(name)
        else:
            name = String(name)
        blockref = BlockRef.from_string(blockref, **kwargs)
        return cls(name, blockref, string)

    def to_html(self, *arg, **kwargs):
        block = self.blockref.get_referenced_block()
        if block:
            inner_html = block.to_html(children=True, *arg, **kwargs)
        else:
            inner_html = self.blockref.to_html(*arg, **kwargs)
        return '<div class="rm-embed-container">' + \
                    inner_html + \
               '</div>'

    def get_tags(self):
        return self.name.get_tags()

    def get_contents(self):
        return self.name.get_contents()

    @classmethod
    def create_pattern(cls, strings=None):
        pats = []
        pats.append("{{embed:\s*%s\s*}}" % BlockRef.create_pattern())
        pats.append("{{\[\[embed\]\]:\s*%s\s*}}" % BlockRef.create_pattern())
        return "|".join(pats)

    def to_string(self):
        if self.string:
            return self.string
        return "{{%s:%s}}" % (self.name.to_string(), self.blockref.to_string())

    def __eq__(self, other):
        return type(self)==type(other) and self.name==other.name and self.blockref==other.blockref


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
            m = re.search(r"([^:]*):(.*)", contents)
            name, text = m.groups()
        else:
            name, text = contents, ""
        return cls(name, text, string)

    def get_tags(self):
        return BlockContent.from_string(self.text).get_tags()

    def get_contents(self):
        return BlockContent.from_string(self.text).get_contents()

    def to_string(self):
        if self.string: return self.string
        if self.text:
            return "{{%s:%s}}" % (self.name, self.text)
        else:
            return "{{%s}}" % self.name

    def to_html(self, *arg, **kwargs):
        return '<button class="bp3-button bp3-small dont-focus-block">%s</button>' % html.escape(self.name)

    @classmethod
    def create_pattern(cls, string=None):
        return "{{.(?:(?<!{{).)*}}" 

    def __eq__(self, other):
        return type(self)==type(other) and self.name==other.name and self.text==other.text


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

    def get_contents(self):
        items = []
        for item in self._title:
            items += item.get_contents()
        return items

    def get_namespace(self):
        return os.path.split(self.title)[0]

    def get_basename(self):
        return os.path.split(self.title)[1]

    def to_string(self):
        if self.string: return self.string
        return f"[[{self.title}]]"

    def to_html(self, title=None, *args, **kwargs):
        #if not title: title=self.title

        # Page ref is just a string
        if title:
            title_html = title
        elif set([type(o) for o in self._title]) == set([String]): 
            title = html.escape(self._title.to_string())
            title_split = title.split("/")
            if len(title_split) == 1:
                title_html = title
            else:
                namespace, name = "/".join(title_split[:-1]) + "/", title_split[-1]
                title_html = \
                    f'<span class="rm-page-ref-namespace">{namespace}</span>'\
                    f'<span class="rm-page-ref-name">{name}</span>'
        else:
            title_html = "".join([o.to_html() for o in self._title])

        uid_attr = f' data-link-uid="{self.uid}"' if self.uid else ''
        return \
            f'<span data-link-title="{html.escape(self.title)}"{uid_attr}>'\
            f'<span class="rm-page-ref-brackets">[[</span>'\
            f'<span class="rm-page-ref rm-page-ref-link-color">{title_html}</span>'\
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

    def __eq__(self, other):
        return type(self)==type(other) and self.title==other.title


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

    def get_contents(self):
        items = []
        for item in self._title:
            items += item.get_contents()
        return items

    def to_string(self):
        if self.string:
            return self.string
        return "#"+self.title

    def to_html(self, *arg, **kwargs):
        return \
            f'<span data-tag="{html.escape(self.title)}" '\
            f'class="rm-page-ref rm-page-ref-tag">#{html.escape(self.title)}</span>'

    @classmethod
    def create_pattern(cls, string):
        pats = ["#[\w\-_@\.]+"]
        # Create pattern for page refs which look like tags
        page_ref_pat = PageRef.create_pattern(string)
        if page_ref_pat:
            pats += ["#"+pat for pat in re.split(RE_SPLIT_OR, page_ref_pat)]

        return "|".join(pats)

    def __eq__(self, other):
        return type(self)==type(other) and self.title == other.title


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
            if block:
                return block.to_string()
        if self.string:
            return self.string
        else:
            return f"(({self.uid}))"

    def to_html(self, *arg, **kwargs):
        block = self.get_referenced_block()
        text = block.to_html() if block else html.escape(self.to_string())
        return '<div class="rm-block-ref"><span>%s</span></div>' % text

    def get_tags(self):
        return []

    @classmethod
    def create_pattern(cls, string=None):
        return "\(\([\w\d\-_]{9}\)\)"

    def get_referenced_block(self):
        if self.roam_db:
            return self.roam_db.query_by_uid(self.uid)

    def __eq__(self, other):
        return type(self)==type(other) and self.uid==other.uid


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
        return f'<span><a href="{html.escape(self.text)}">{html.escape(self.text)}</a></span>'

    def __eq__(self, other):
        return type(self)==type(other) and self.text==other.text


class String(BlockContentItem):
    def __init__(self, string):
        if type(string) == String:
            string == string.to_string()
        self.string = string

    @classmethod
    def from_string(cls, string, validate=True, **kwargs):
        super().from_string(string, validate)
        return cls(string)

    @classmethod
    def validate_string(cls, string):
        return True

    def to_html(self, *arg, **kwargs):
        return html.escape(self.to_string()).replace("\n", "<br>")

    def get_tags(self):
        return []

    def to_string(self):
        return self.string

    def __eq__(self, other):
        return type(self)==type(other) and self.string==other.string


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
        return '<span><strong>%s:</strong></span>' % html.escape(self.title)

    def get_tags(self):
        return [self.title]

    def to_string(self):
        if self.string:
            return self.string
        return self.title+"::"

    def __eq__(self, other):
        return type(self)==type(other) and self.title==other.title


if __name__ == "__main__":
    text = """```javascript
    x = () => { return 'hello world' }
    x() ` aweawe `
    ```
    aweawef
    ```"""
    pat = "```"
    res = list(re.finditer(pat, text))

    supported_languages = ["javascript"]

    content = []
    string_start = 0
    while len(res) > 2:
        code_start, code_end = res.pop(0), res.pop(0)
        code_block = text[code_start.start():code_end.end()]
        code = text[code_start.end():code_end.start()]
        try:
            first_line = re.search("^.*\n", code).group().strip()
            language = first_line if first_line in supported_languages else None
        except AttributeError:
            language = None
        content.append(String(text[string_start:code_start.start()]))
        content.append(CodeBlock(code, language, code_block))
        string_start = code_end.end()
    content.append(String(text[string_start:]))
            

    print(content)
    
