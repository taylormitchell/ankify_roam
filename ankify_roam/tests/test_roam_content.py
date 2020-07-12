import unittest 
import logging
from ankify_roam import anki, roam
from ankify_roam.roam.containers import Block
from ankify_roam.roam.content import * 

# TODO: all RoamObject types should implement the interface

class TestBlockContent(unittest.TestCase):
    def test_find_and_replace(self):
        """
        Roam Object Coverage
        Cloze: 
        Image:
        Alias: 1,
        CodeBlock: 2,
        Checkbox: 1,
        View:
        Button:
        PageRef: 1,2
        PageTag: 1,2
        BlockRef: 1,2,3
        """
        # Test 1 
        string = "{{[[TODO]]}} something [this]([[This]]) [[Saturday]] about ((ZtmwW4k32)) #Important"
        a = BlockContent.from_string(string)
        b = BlockContent([
            Checkbox(False),
            String(" something "),
            Alias("this",PageRef("This")),
            String(" "),
            PageRef("Saturday"),
            String(" about "),
            BlockRef("ZtmwW4k32"),
            String(" "),
            PageTag("Important")
        ])
        self.assertListEqual(a, b)
        tags = ["TODO","This","Saturday","Important"]
        self.assertSetEqual(set(a.get_tags()), set(tags))

        # Test 2 
        string = "\n".join([
            "```clojure",
            "www.google.com",
            "[[page]]",
            "((E-j9hXq0m))```"])
        a = BlockContent.from_string(string)
        b = BlockContent([
            CodeBlock("www.google.com\n[[page]]\n((E-j9hXq0m))","clojure"),
        ])
        self.assertListEqual(a, b)

        # Test 3
        string = "Some block refs: ((5xB8JO-xg)) #temp #[[anki_note]]"
        a = BlockContent.from_string(string)
        b = BlockContent([
            String("Some block refs: "), 
            BlockRef("5xB8JO-xg"),
            String(" "), 
            PageTag.from_string("#temp"), 
            String(" "), 
            PageTag.from_string("#[[anki_note]]"), 
        ])
        self.assertListEqual(a, b)


    def test_get_tags(self):
        string = "Something with [[page refs]] and #some #[[tags]]"
        tags = sorted(BlockContent.from_string(string).get_tags())
        self.assertListEqual(tags, ["page refs","some","tags"])


class TestCloze(unittest.TestCase):
    def setUp(self):
        self.maxDiff = 1000

    def test_from_string(self):
        string = "{text}"
        cloze = Cloze.from_string(string)
        self.assertEqual(cloze.text, "text")
        
        string = "{1:text}"
        cloze = Cloze.from_string(string)
        self.assertEqual(cloze.id, 1)
        self.assertEqual(cloze.text, "text")

        string = "{c1:text}"
        cloze = Cloze.from_string(string)
        self.assertEqual(cloze.id, 1)
        self.assertEqual(cloze.text, "text")

        string = "{c1|text}"
        cloze = Cloze.from_string(string)
        self.assertEqual(cloze.id, 1)
        self.assertEqual(cloze.text, "text")

        string = "text"
        self.assertRaises(ValueError, Cloze.from_string, string)

        string = "{text} and {more text}"
        self.assertRaises(ValueError, Cloze.from_string, string)

        string = "{{button}}"
        self.assertRaises(ValueError, Cloze.from_string, string)

        string = "[[{]]text[[}]]"
        cloze = Cloze.from_string(string)
        self.assertEqual(cloze.text, "text")
        
        string = "[[{1:]]text[[}]]"
        cloze = Cloze.from_string(string)
        self.assertEqual(cloze.id, 1)
        self.assertEqual(cloze.text, "text")

        string = "[[{5]]text[[}]]"
        cloze = Cloze.from_string(string)
        self.assertEqual(cloze.id, 5)
        self.assertEqual(cloze.text, "text")

        string = "[[{99:]]text[[}]]"
        cloze = Cloze.from_string(string)
        self.assertEqual(cloze.id, 99)
        self.assertEqual(cloze.text, "text")

        string = "[[{c1:]]text[[}]]"
        cloze = Cloze.from_string(string)
        self.assertEqual(cloze.id, 1)
        self.assertEqual(cloze.text, "text")

        string = "\n".join(["{te","xt}"])
        cloze = Cloze.from_string(string)
        self.assertEqual(cloze.text, "\n".join(["te","xt"]))

    def test_find_and_replace(self):
        a = Cloze.find_and_replace("Something with a {cloze}")
        b = [String("Something with a "), Cloze(1, "cloze")]
        self.assertListEqual(a, b)

    def test_to_string(self):
        self.assertTrue(Cloze(1, "text").to_string(), "{{c1::text}}")
        self.assertTrue(Cloze(1, "text").to_string(style="anki"), "{{c1::text}}")
        self.assertTrue(Cloze(1, "text").to_string(style="roam"), "{c1:text}")
        self.assertRaises(ValueError, Cloze(1, "text").to_string, "derp")

    def test_to_html(self):
        self.assertTrue(Cloze(1,"text").to_html(), "{{c1:text}}")
        a = Cloze(1,"[[page]]").to_html(pageref_cloze="outside")
        b = \
            '{{c1::'\
            '<span data-link-title="page">'\
            '<span class="rm-page-ref-brackets">[[</span>'\
            '<span tabindex="-1" class="rm-page-ref rm-page-ref-link-color">page</span>'\
            '<span class="rm-page-ref-brackets">]]</span></span>'\
            '}}'
        self.assertEqual(a, b)
        a = Cloze(1,"[[page]]").to_html(pageref_cloze="inside")
        b = \
            '<span data-link-title="page">'\
            '<span class="rm-page-ref-brackets">[[</span>'\
            '<span tabindex="-1" class="rm-page-ref rm-page-ref-link-color">{{c1::page}}</span>'\
            '<span class="rm-page-ref-brackets">]]</span></span>'
        self.assertEqual(a, b)
        a = Cloze(1,"[[namespace/base]]").to_html(pageref_cloze="base_only")
        b = \
            '<span data-link-title="namespace/base">'\
            '<span class="rm-page-ref-brackets">[[</span>'\
            '<span tabindex="-1" class="rm-page-ref rm-page-ref-link-color">namespace/{{c1::base}}</span>'\
            '<span class="rm-page-ref-brackets">]]</span></span>'
        self.assertEqual(a, b)

        a = Cloze.from_string("[[{c2:]]something[[}]]").to_html(proc_cloze=False)
        b = '<span data-link-title="{c2:">'\
            '<span class="rm-page-ref-brackets">[[</span>'\
            '<span tabindex="-1" class="rm-page-ref rm-page-ref-link-color">{c2:</span>'\
            '<span class="rm-page-ref-brackets">]]</span></span>'\
            'something'\
            '<span data-link-title="}">'\
            '<span class="rm-page-ref-brackets">[[</span>'\
            '<span tabindex="-1" class="rm-page-ref rm-page-ref-link-color">}</span>'\
            '<span class="rm-page-ref-brackets">]]</span></span>'
        self.assertEqual(a, b)

        a = Cloze.from_string("{c2:something}").to_html(proc_cloze=False)
        b = "{c2:something}"
        self.assertEqual(a, b)

        a = Cloze.from_string("{c2|something}").to_html(proc_cloze=False)
        b = "{c2|something}"
        self.assertEqual(a, b)

    def test_get_tags(self):
        cloze = Cloze(1, "Something with [[page refs]] and #some #[[tags]]")
        self.assertListEqual(sorted(cloze.get_tags()), ["page refs","some","tags"])

    def test_assign_cloze_ids(self):
        clozes = [Cloze(None, "no id"), Cloze(6, "has id"), Cloze(1, "has id"), 
                  Cloze(None, "no id"), Cloze(3, "also has id")]
        Cloze._assign_cloze_ids(clozes)
        cloze_ids = [c.id for c in clozes]
        self.assertListEqual(cloze_ids, [2,6,1,4,3])


class TestImage(unittest.TestCase):
    def test_from_string(self):
        img = Image.from_string("![](www.google.com/image.png)")
        self.assertEqual(img.src, "www.google.com/image.png")
        self.assertEqual(img.alt, "")

        img = Image.from_string("![text](www.google.com/image.png)")
        self.assertEqual(img.src, "www.google.com/image.png")
        self.assertEqual(img.alt, "text")

        string = "![text](www.google.com)/image.png)"
        self.assertRaises(ValueError, Image.from_string, string)
        string = "[text](www.google.com/image.png)"
        self.assertRaises(ValueError, Image.from_string, string)
        string = "![]()"
        self.assertRaises(ValueError, Image.from_string, string)
        string = "\n".join(["![](www.go","ogle.com/image.png)"])
        self.assertRaises(ValueError, Image.from_string, string)

    def test_find_and_replace(self):
        string = "something with an ![](image.png) in it"
        a = Image.find_and_replace(string)
        b = BlockContent([
            String("something with an "),
            Image("image.png"),
            String(" in it")
        ])
        self.assertEqual(a, b)

    def test_to_string(self):
        a = Image("www.google.com/image.png", "text").to_string()
        b = "![text](www.google.com/image.png)"
        self.assertEqual(a, b)

        a = Image("www.google.com/image.png", "te\nxt").to_string()
        b = "![te\nxt](www.google.com/image.png)"
        self.assertEqual(a, b)

    def test_to_html(self):
        a = Image("https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png", "alt").to_html()
        b = '<img src="https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png" alt="alt" draggable="false" class="rm-inline-img">'
        self.assertEqual(a, b)

    def test_get_tags(self):
        a = Image("www.google.com/image.png", "text").get_tags()
        b = []
        self.assertListEqual(a, b)


class TestAlias(unittest.TestCase):
    def test_from_string(self):
        string = "[something](www.google.com)"
        alias = Alias.from_string(string)
        self.assertEqual(alias.alias, "something")
        self.assertEqual(alias.destination, String("www.google.com"))

        string = "[something]([[page]])"
        alias = Alias.from_string(string)
        self.assertEqual(alias.alias, "something")
        self.assertEqual(alias.destination, PageRef("page"))

        string = "[something](((LtKPM-UZe)))"
        alias = Alias.from_string(string)
        self.assertEqual(alias.alias, "something")
        self.assertEqual(alias.destination, BlockRef("LtKPM-UZe"))

        # Can have newline in alias
        string = "\n".join(["[somet","hing](www.google.com)"])
        alias = Alias.from_string(string)
        self.assertEqual(alias.alias, "\n".join(["somet","hing"]))
        self.assertEqual(alias.destination, String("www.google.com"))

        string = "[](www.google.com)"
        self.assertRaises(ValueError, Alias.from_string, string)

        string = "[something[]](www.google.com)"
        self.assertRaises(ValueError, Alias.from_string, string)

        string = "[something]()"
        self.assertRaises(ValueError, Alias.from_string, string)

        string = "[something](www.google.com[)"
        self.assertRaises(ValueError, Alias.from_string, string)

        string = "[something](www.google.com) and something)"
        self.assertRaises(ValueError, Alias.from_string, string)

    def test_find_and_replace(self):
        a = Alias.find_and_replace("something [link]([[page]]) to something")
        b = [String("something "),Alias("link",PageRef("page")),String(" to something")]
        self.assertListEqual(a, b)

    def test_to_string(self):
        link = Alias("text", Url("www.google.com"))
        self.assertEqual(link.to_string(), "[text](www.google.com)")
        link = Alias("text", PageRef("some page"))
        self.assertEqual(link.to_string(), "[text]([[some page]])")
        link = Alias("text", BlockRef("y3LFc4rFK"))
        self.assertEqual(link.to_string(), "[text](((y3LFc4rFK)))")

    def test_to_html(self):
        # Alias to roam page
        a = Alias("text", PageRef("page")).to_html()
        b = '<a title="page: page" class="rm-alias rm-alias-page">text</a>'
        self.assertEqual(a, b)

        # Alias to roam block
        class RoamGraphProxy:
            def query_by_uid(self, uid):
                return Block.from_string("{{[[TODO]]}} some block with a [[page]] ref and a #tag")
        a = Alias("text", BlockRef("y3LFc4rFK", roam_db=RoamGraphProxy())).to_html()
        b = '<a title="block: {{[[TODO]]}} some block with a [[page]] ref and a #tag" class="rm-alias rm-alias-block">text</a>'
        self.assertEqual(a, b)

        # Alias to web page
        a = Alias("text", Url("www.google.com")).to_html()
        b = '<a title="url: www.google.com" class="rm-alias rm-alias-external" href="www.google.com">text</a>'
        self.assertEqual(a, b)

    def test_get_tags(self):
        a = Alias("text",PageRef("page")).get_tags()
        b = ["page"]
        self.assertListEqual(a, b)


class TestCodeBlock(unittest.TestCase):
    def test_from_string(self):
        string = "```clojure\ndef foo(x+y):\n    return x+y```"
        language = 'clojure'
        code = 'def foo(x+y):\n    return x+y'
        cb = CodeBlock.from_string(string)
        self.assertEqual(cb.language, language)
        self.assertEqual(cb.code, code)

        string = "```css\n.rm-page-ref-tag{\n  display:none;\n}```"
        language = 'css'
        code = '.rm-page-ref-tag{\n  display:none;\n}'
        cb = CodeBlock.from_string(string)
        self.assertEqual(cb.language, language)
        self.assertEqual(cb.code, code)

        string = "```python\ndef foo(x+y):\n    return x+y```"
        language = None
        code = 'python\ndef foo(x+y):\n    return x+y'
        cb = CodeBlock.from_string(string)
        self.assertEqual(cb.language, language)
        self.assertEqual(cb.code, code)

        string = "```\ndef foo(x+y):\n    return x+y```"
        language = None
        code = '\ndef foo(x+y):\n    return x+y'
        cb = CodeBlock.from_string(string)
        self.assertEqual(cb.language, language)
        self.assertEqual(cb.code, code)

        string = "```def foo(x+y):\n    return x+y```"
        language = None
        code = 'def foo(x+y):\n    return x+y'
        cb = CodeBlock.from_string(string)
        self.assertEqual(cb.language, language)
        self.assertEqual(cb.code, code)

    def test_find_and_replace(self):
        string = "something something ```clojure\ndef foo(x+y):\n    return x+y```"
        a = CodeBlock.find_and_replace(string)
        b = BlockContent([
                String("something something "), 
                CodeBlock('def foo(x+y):\n    return x+y',"clojure")])
        self.assertListEqual(a, b)

    def test_to_string(self):
        a = CodeBlock("def foo():\n    print('foo')", "clojure").to_string()
        b = "```clojure\ndef foo():\n    print('foo')```"
        self.assertEqual(a, b)

    def test_to_html(self):
        a = CodeBlock("def foo(x+y):\n    return x+y", "clojure").to_html()
        b = "<pre>def foo(x+y):<br>    return x+y</pre>"
        self.assertEqual(a, b)

    def test_get_tags(self): 
        a = CodeBlock("def foo():\n    #[[tag]]", "clojure").get_tags()
        b = []
        self.assertListEqual(a, b)


class TestCheckbox(unittest.TestCase):
    def test_from_string(self):
        string = "{{[[TODO]]}}"
        self.assertFalse(Checkbox.from_string(string).checked)
        string = "{{[[DONE]]}}"
        self.assertTrue(Checkbox.from_string(string).checked)
        string = "{{[[TODO]]}} some text"
        self.assertRaises(ValueError, Checkbox.from_string, string)
        string = "{{TODO}}"
        self.assertRaises(ValueError, Checkbox.from_string, string)

    def test_find_and_replace(self):
        roam_objects = BlockContent.from_string("{{[[TODO]]}} thing to do")
        a = Checkbox.find_and_replace(roam_objects)
        b = [Checkbox(checked=False), String(" thing to do")]
        self.assertListEqual(a, b)

    def test_to_string(self):
        self.assertEqual(Checkbox(True).to_string(), "{{[[DONE]]}}")
        self.assertEqual(Checkbox(False).to_string(), "{{[[TODO]]}}")

    def test_to_html(self):
        checkbox = Checkbox.from_string("{{[[TODO]]}}")
        a = checkbox.to_html()
        b = '<span><label class="check-container"><input type="checkbox"><span class="checkmark"></span></label></span>'
        self.assertEqual(a, b)
        checkbox = Checkbox.from_string("{{[[DONE]]}}")
        a = checkbox.to_html()
        b = '<span><label class="check-container"><input type="checkbox" checked=""><span class="checkmark"></span></label></span>'
        self.assertEqual(a, b)

    def test_get_tags(self):
        checkbox = Checkbox.from_string("{{[[TODO]]}}")
        self.assertListEqual(checkbox.get_tags(), ["TODO"])
        checkbox = Checkbox.from_string("{{[[DONE]]}}")
        self.assertListEqual(checkbox.get_tags(), ["DONE"])


class TestView(unittest.TestCase):
    def test_from_string(self):
        embed = View.from_string("{{[[embed]]:((hh2wTNsMz))}}")
        self.assertEqual(embed.name, PageRef("embed"))
        self.assertEqual(embed.text, "((hh2wTNsMz))")

        youtube = View.from_string("{{[[youtube]]:www.youtube.com}}")
        self.assertEqual(youtube.name, PageRef("youtube"))
        self.assertEqual(youtube.text, "www.youtube.com")

        query = View.from_string("{{[[query]]:{and:[[page]][[tag]]}}}")
        self.assertEqual(query.name, PageRef("query"))
        self.assertEqual(query.text, "{and:[[page]][[tag]]}")

        mentions = View.from_string("{{[[mentions]]:[[page]]}}")
        self.assertEqual(mentions.name, PageRef("mentions"))
        self.assertEqual(mentions.text, "[[page]]")

        embed = View.from_string("{{embed:((hh2wTNsMz))}}")
        self.assertEqual(embed.name, String("embed"))
        self.assertEqual(embed.text, "((hh2wTNsMz))")

        youtube = View.from_string("{{youtube:www.youtube.com}}")
        self.assertEqual(youtube.name, String("youtube"))
        self.assertEqual(youtube.text, "www.youtube.com")

        query = View.from_string("{{query:{and:[[page]][[tag]]}}}")
        self.assertEqual(query.name, String("query"))
        self.assertEqual(query.text, "{and:[[page]][[tag]]}")

        mentions = View.from_string("{{mentions:[[page]]}}")
        self.assertEqual(mentions.name, String("mentions"))
        self.assertEqual(mentions.text, "[[page]]")

        string = "\n".join(["{{query:{and:[[pa","ge]]}}}"])
        self.assertRaises(ValueError, View.from_string, string)

    def test_find_and_replace(self):
        string = "here's a {{query: {and:[[page]]}}}"
        a = View.find_and_replace(string)
        b = BlockContent([
            String("here's a "),
            View("query"," {and:[[page]]}")
        ])
        self.assertListEqual(a,b)

    def to_string(self):
        a = View("embed", "some text").to_string()
        b = "{{embed:some text}}"
        self.assertEqual(a, b)

    def test_to_html(self):
        string = "{{[[embed]]: ((hh2wTNsMz))}}"
        view = View.from_string(string)
        self.assertEqual(view.to_string(), string)

        string = "{{[[query]]: {and: [[ex-A]] [[ex-B]]}}}"
        view = View.from_string(string)
        self.assertEqual(view.to_string(), string)

        string = "{{[[mentions]]: [[page]]}}"
        view = View.from_string(string)
        self.assertEqual(view.to_string(), string)

        string = "{{[[youtube]]: www.youtube.com}}"
        view = View.from_string(string)
        self.assertEqual(view.to_string(), string)

    def test_get_tags(self):
        a = View.from_string("{{[[query]]:some text}}").get_tags()
        b = ["query"]
        self.assertListEqual(a, b)


class TestButton(unittest.TestCase):
    def test_from_string(self):
        a = Button.from_string("{{text}}")
        self.assertEqual(a.name, "text")
        self.assertEqual(a.text, "")
        a = Button.from_string("{{text: with more text}}")
        self.assertEqual(a.name, "text")
        self.assertEqual(a.text, " with more text")
        a = Button.from_string("{{text: with a colon ':' in the text part}}")
        self.assertEqual(a.name, "text")
        self.assertEqual(a.text, " with a colon ':' in the text part")

        string = "\n".join(["{{te","xt}}"])
        self.assertRaises(ValueError, Button.from_string, string)

    def test_find_and_replace(self):
        string = "here's a {{Button}} and {{another: with stuff}}"
        a = Button.find_and_replace(string)
        b = BlockContent([
            String("here's a "),
            Button("Button"),
            String(" and "),
            Button("another", " with stuff"),
        ])
        self.assertListEqual(a,b)

    def test_to_string(self):
        a = Button("text")
        self.assertEqual(a.to_string(), "{{text}}")

    def test_to_html(self):
        a = Button("name").to_html()
        b = '<button class="bp3-button bp3-small dont-focus-block">name</button>'
        self.assertEqual(a, b)
        a = Button("name", "with some other name").to_html()
        b = '<button class="bp3-button bp3-small dont-focus-block">name</button>'
        self.assertEqual(a, b)

    def test_get_tags(self):
        a = Button("text", "text with [[tags]] in [[it]]").get_tags()
        b = ["tags","it"]
        self.assertSetEqual(set(a), set(b))


class TestPageRef(unittest.TestCase):
    def test_from_string(self):
        a = PageRef.from_string("[[page]]").title
        b = "page"
        self.assertEqual(a, b)

        a = PageRef.from_string("[[page in [[a [[page]]]] man]]").title
        b = "page in [[a [[page]]]] man"
        self.assertEqual(a, b)

        string = "\n".join(["[[pa","ge]]"])
        a = PageRef.from_string(string).title
        b = string[2:-2]
        self.assertEqual(a, b)

    def test_find_and_replace(self):
        x = PageRef("sting")
        string = "something with a [[couple]] of [[pages]] in it"
        a = PageRef.find_and_replace(string)
        b = BlockContent([
            String("something with a "), 
            PageRef("couple"), 
            String(" of "), 
            PageRef("pages"), 
            String(" in it")
        ])
        self.assertListEqual(a, b)

    def test_to_string(self):
        a = PageRef("page").to_string()
        b = "[[page]]"
        self.assertEqual(a, b)

    def test_to_html(self):
        a = PageRef("page", "PMXeggRpU").to_html()
        b = '<span data-link-title="page" data-link-uid="PMXeggRpU">'\
            '<span class="rm-page-ref-brackets">[[</span>'\
            '<span tabindex="-1" class="rm-page-ref rm-page-ref-link-color">page</span>'\
            '<span class="rm-page-ref-brackets">]]</span></span>'
        self.assertEqual(a, b)
        a = PageRef("page").to_html()
        b = '<span data-link-title="page">'\
            '<span class="rm-page-ref-brackets">[[</span>'\
            '<span tabindex="-1" class="rm-page-ref rm-page-ref-link-color">page</span>'\
            '<span class="rm-page-ref-brackets">]]</span></span>'
        self.assertEqual(a, b)

    def test_get_tags(self):
        a = PageRef("[[page in a [[page]]]]ness").get_tags()
        b = ["[[page in a [[page]]]]ness","page in a [[page]]", "page"]
        self.assertSetEqual(set(a), set(b))


class TestPageTag(unittest.TestCase):
    def test_from_string(self):
        a = PageTag.from_string("#[[page]]").title
        b = "page"
        self.assertEqual(a, b)

        a = PageTag.from_string("#page").title
        b = "page"
        self.assertEqual(a, b)

        string = "\n".join(["#[[pa","ge]]"])
        a = PageTag.from_string(string).title
        b = string[3:-2]
        self.assertEqual(a, b)

    def test_find_and_replace(self):
        string = "something with [[some]] #[[tags]] in #it"
        a = PageTag.find_and_replace(string)
        b = BlockContent([
            String("something with [[some]] "), 
            PageTag.from_string("#[[tags]]"), 
            String(" in "), 
            PageTag("it"), 
        ])
        self.assertListEqual(a, b)


    def test_to_string(self):
        a = PageTag("page").to_string()
        b = "#page"
        self.assertEqual(a, b)

        a = PageTag.from_string("#[[page]]").to_string()
        b = "#[[page]]"
        self.assertEqual(a, b)

    def test_to_html(self):
        a = PageTag("tag").to_html()
        b = '<span tabindex="-1" data-tag="tag" class="rm-page-ref rm-page-ref-tag">#tag</span>'
        self.assertEqual(a, b)
        a = PageTag.from_string("#[[tag]]").to_html()
        b = '<span tabindex="-1" data-tag="tag" class="rm-page-ref rm-page-ref-tag">#tag</span>'
        self.assertEqual(a, b)
        a = PageTag.from_string("#[[[[tag]]:((cdYtyouxk))]]").to_html()
        b = '<span tabindex="-1" data-tag="[[tag]]:((cdYtyouxk))" class="rm-page-ref rm-page-ref-tag">#[[tag]]:((cdYtyouxk))</span>'
        self.assertEqual(a, b)
        a = PageTag.from_string("#[[[[source]]:[[some book]]]]").to_html()
        b = '<span tabindex="-1" data-tag="[[source]]:[[some book]]" class="rm-page-ref rm-page-ref-tag">#[[source]]:[[some book]]</span>'
        self.assertEqual(a, b)

    def test_get_tags(self):
        a = PageTag("[[page in a [[page]]]]ness").get_tags()
        b = ["[[page in a [[page]]]]ness","page in a [[page]]", "page"]
        self.assertSetEqual(set(a), set(b))


class TestBlockRef(unittest.TestCase):
    def setUp(self):
        class RoamGraphProxy:
            def query_by_uid(self, uid):
                blocks = {
                    "mZPhN5wFj": Block.from_string("some block"),
                    "LWGXbhfz_": Block.from_string("{{[[TODO]]}} some block with a [[page]] ref and a #tag") 
                }
                return blocks[uid]
        self.roam_db = RoamGraphProxy()

    def test_from_string(self):
        a = BlockRef.from_string("((LWGXbhfz_))", roam_db=self.roam_db).uid
        b = "LWGXbhfz_"
        self.assertEqual(a, b)

    def test_find_and_replace(self):
        string = "something with a ((4MxiXZn9f)) in #it"
        a = BlockRef.find_and_replace(string)
        b = BlockContent([
            String("something with a "), 
            BlockRef("4MxiXZn9f"), 
            String(" in #it"), 
        ])
        self.assertListEqual(a, b)

    def test_to_string(self):
        a = BlockRef("LWGXbhfz_", self.roam_db).to_string(expand=False)
        b = "((LWGXbhfz_))"
        self.assertEqual(a, b)

        a = BlockRef("LWGXbhfz_", self.roam_db).to_string(expand=True)
        b = "{{[[TODO]]}} some block with a [[page]] ref and a #tag"
        self.assertEqual(a, b)

    def test_to_html(self):
        a = BlockRef("mZPhN5wFj", self.roam_db).to_html()
        b = '<div class="rm-block-ref"><span>some block</span></div>'
        self.assertEqual(a, b)
        a = BlockRef("LWGXbhfz_", self.roam_db).to_html()
        b = '<div class="rm-block-ref"><span><span><label class="check-container">'\
            '<input type="checkbox"><span class="checkmark"></span></label></span>'\
            ' some block with a <span data-link-title="page">'\
            '<span class="rm-page-ref-brackets">[[</span><span tabindex="-1" '\
            'class="rm-page-ref rm-page-ref-link-color">page</span><span '\
            'class="rm-page-ref-brackets">]]</span></span> ref and a <span '\
            'tabindex="-1" data-tag="tag" class="rm-page-ref rm-page-ref-tag">'\
            '#tag</span></span></div>'
        self.assertEqual(a, b)

    def test_get_tags(self):
        a = BlockRef("LWGXbhfz_", self.roam_db).get_tags()
        b = []
        self.assertListEqual(a, b)


class TestUrl(unittest.TestCase):
    def test_to_html(self):
        a = Url("http://www.google.com").to_html()
        b = '<span><a href="http://www.google.com">http://www.google.com</a></span>'
        self.assertEqual(a, b)


class TestAttribute(unittest.TestCase):
    def test_from_string(self):
        a = Attribute.from_string("attr::").title
        b = "attr"
        self.assertEqual(a,b)

        string = "\n".join(["attri","bute::"])
        a = Attribute(string).title
        b = string
        self.assertEqual(a,b)

    def test_find_and_replace(self):
        string = "attribute:: text"
        a = Attribute.find_and_replace(string)
        b = BlockContent([Attribute("attribute"), String(" text")])
        self.assertListEqual(a,b)

        string = "attribute:::: text"
        a = Attribute.find_and_replace(string)
        b = BlockContent([Attribute("attribute"), String(":: text")])
        self.assertListEqual(a,b)

    def test_to_string(self):
        a = Attribute("attr").to_string()
        b = "attr::"
        self.assertEqual(a,b)

    def test_to_html(self):
        a = Attribute("attribute").to_html()
        b = '<span><strong tabindex="-1" style="cursor: pointer;">attribute:</strong></span>'
        self.assertEqual(a,b)

    def test_get_tags(self):
        a = Attribute("attr").get_tags()
        b = ["attr"]
        self.assertListEqual(a,b)


if __name__=="__main__":
    unittest.main()
