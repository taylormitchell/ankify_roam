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

class TestBlockQuote(unittest.TestCase):
    def test_from_string(self):
        string = "> here's a quote"
        block_quote = BlockQuote.from_string(string)
        self.assertEqual(block_quote.block_content.to_string(), "here's a quote")


class TestCloze(unittest.TestCase):
    def setUp(self):
        self.maxDiff = 1000

    def test_from_string(self):
        string = "{text}"
        cloze = Cloze.from_string(string)
        self.assertEqual(cloze.inner.to_string(), "text")
        
        string = "{1:text}"
        cloze = Cloze.from_string(string)
        self.assertEqual(cloze.id, 1)
        self.assertEqual(cloze.inner.to_string(), "text")

        string = "{c1:text}"
        cloze = Cloze.from_string(string)
        self.assertEqual(cloze.id, 1)
        self.assertEqual(cloze.inner.to_string(), "text")

        string = "{c1|text}"
        cloze = Cloze.from_string(string)
        self.assertEqual(cloze.id, 1)
        self.assertEqual(cloze.inner.to_string(), "text")

        string = "text"
        self.assertRaises(ValueError, Cloze.from_string, string)

        string = "{text} and {more text}"
        self.assertRaises(ValueError, Cloze.from_string, string)

        string = "{{button}}"
        self.assertRaises(ValueError, Cloze.from_string, string)

        string = "[[{]]text[[}]]"
        cloze = Cloze.from_string(string)
        self.assertEqual(cloze.inner.to_string(), "text")
        
        string = "[[{1:]]text[[}]]"
        cloze = Cloze.from_string(string)
        self.assertEqual(cloze.id, 1)
        self.assertEqual(cloze.inner.to_string(), "text")

        string = "[[{5]]text[[}]]"
        cloze = Cloze.from_string(string)
        self.assertEqual(cloze.id, 5)
        self.assertEqual(cloze.inner.to_string(), "text")

        string = "[[{99:]]text[[}]]"
        cloze = Cloze.from_string(string)
        self.assertEqual(cloze.id, 99)
        self.assertEqual(cloze.inner.to_string(), "text")

        string = "[[{c1:]]text[[}]]"
        cloze = Cloze.from_string(string)
        self.assertEqual(cloze.id, 1)
        self.assertEqual(cloze.inner.to_string(), "text")

        string = "\n".join(["{te","xt}"])
        cloze = Cloze.from_string(string)
        self.assertEqual(cloze.inner.to_string(), "\n".join(["te","xt"]))

        string = "[[{c1:]]text[[::hint}]]"
        cloze = Cloze.from_string(string)
        self.assertEqual(cloze.id, 1)
        self.assertEqual(cloze.inner.to_string(), "text")

    def test_hint(self):
        string = "{text::hint}"
        cloze = Cloze.from_string(string)
        self.assertEqual(cloze.hint.text, "hint")

        string = "{text[[::hint in page ref]]}"
        cloze = Cloze.from_string(string)
        self.assertEqual(cloze.hint.text, "hint in page ref")

        string = "[[{]]text[[::hint in page ref]][[}]]"
        cloze = Cloze.from_string(string)
        self.assertEqual(cloze.hint.text, "hint in page ref")

        string = "[[{]]text[[::hint in closing page ref}]]"
        cloze = Cloze.from_string(string)
        self.assertEqual(cloze.hint.text, "hint in closing page ref")

        string = "{text::hint with double colons :: in it}"
        cloze = Cloze.from_string(string)
        self.assertEqual(cloze.hint.text, "hint with double colons :: in it")

    def test_find_and_replace(self):
        a = Cloze.find_and_replace("Something with a {cloze}")
        b = [String("Something with a "), Cloze("cloze", id=1)]
        self.assertListEqual(a, b)

    def test_clozed_code(self):
        res = Cloze.find_and_replace("Something with a {c1:cloze with `code` inside} it")
        exp = BlockContent([
            String("Something with a "), 
            Cloze(
                inner=BlockContent([String("cloze with "), CodeInline("code"), String(" inside")]), 
                c=True, id=1, sep=":"),
            String(" it"), 
            ])
        self.assertListEqual(res, exp)

    def test_to_string(self):
        self.assertTrue(Cloze("text", id=1, c=True).to_string(), "{{c1::text}}")
        self.assertTrue(Cloze("text", id=1).to_string(), "{{1::text}}")
        self.assertTrue(Cloze("text").to_string(), "{{1::text}}")
        self.assertTrue(Cloze("text", id=1, c=True).to_string(style="anki"), "{{c1::text}}")
        self.assertTrue(Cloze("text", id=1, c=True).to_string(style="roam"), "{c1:text}")
        self.assertTrue(Cloze("text", id=1, c=True, hint="hint").to_string(style="anki"), "{{c1::text::hint}}")
        self.assertRaises(ValueError, Cloze("text", id=1).to_string, "text")

    def test_to_html(self):
        self.assertTrue(Cloze("text", id=1).to_html(), "{{c1:text}}")

        a = Cloze.from_string("{text}").to_html()
        b = "{{c1::text}}"
        self.assertEqual(a, b)

        a = Cloze.from_string("{3|text}").to_html()
        b = "{{c3::text}}"
        self.assertEqual(a, b)

        a = Cloze.from_string("[[{3|]]text[[}]]").to_html()
        b = "{{c3::text}}"
        self.assertEqual(a, b)

        a = Cloze.from_string("{c2:something}").to_html(proc_cloze=False)
        b = "{c2:something}"
        self.assertEqual(a, b)

        a = Cloze.from_string("{c2|something}").to_html(proc_cloze=False)
        b = "{c2|something}"
        self.assertEqual(a, b)

        a = Cloze.from_string("[[{c2]]something[[}]]").to_html(proc_cloze=False)
        b = BlockContent([PageRef("{c2"), String("something"), PageRef("}")]).to_html()
        self.assertEqual(a, b)

    def test_single_page_to_html(self):
        a = Cloze(PageRef("page")).to_html(pageref_cloze="outside")
        b = \
            '{{c1::'\
            '<span data-link-title="page">'\
            '<span class="rm-page-ref-brackets">[[</span>'\
            '<span class="rm-page-ref rm-page-ref-link-color">page</span>'\
            '<span class="rm-page-ref-brackets">]]</span></span>'\
            '}}'
        self.assertEqual(a, b)

        a = Cloze(PageRef("page")).to_html(pageref_cloze="inside")
        b = \
            '<span data-link-title="page">'\
            '<span class="rm-page-ref-brackets">[[</span>'\
            '<span class="rm-page-ref rm-page-ref-link-color">{{c1::page}}</span>'\
            '<span class="rm-page-ref-brackets">]]</span></span>'
        self.assertEqual(a, b)

        a = Cloze(PageRef("namespace/base")).to_html(pageref_cloze="base_only")
        b = \
            '<span data-link-title="namespace/base">'\
            '<span class="rm-page-ref-brackets">[[</span>'\
            '<span class="rm-page-ref rm-page-ref-link-color">namespace/{{c1::base}}</span>'\
            '<span class="rm-page-ref-brackets">]]</span></span>'
        self.assertEqual(a, b)

        a = Cloze.from_string("[[{c2:]]something[[}]]").to_html(proc_cloze=False)
        b = '<span data-link-title="{c2:">'\
            '<span class="rm-page-ref-brackets">[[</span>'\
            '<span class="rm-page-ref rm-page-ref-link-color">{c2:</span>'\
            '<span class="rm-page-ref-brackets">]]</span></span>'\
            'something'\
            '<span data-link-title="}">'\
            '<span class="rm-page-ref-brackets">[[</span>'\
            '<span class="rm-page-ref rm-page-ref-link-color">}</span>'\
            '<span class="rm-page-ref-brackets">]]</span></span>'
        self.assertEqual(a, b)

    def test_get_tags(self):
        content = BlockContent.from_string("Something with [[page refs]] and #some #[[tags]]")
        cloze = Cloze(content)
        self.assertListEqual(sorted(cloze.get_tags()), ["page refs","some","tags"])

    def test_assign_cloze_ids(self):
        clozes = [Cloze("no id", id=None), Cloze("has id", id=6), Cloze("has id", id=1), 
                  Cloze("no id", id=None), Cloze("also has id", id=3)]
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
        self.assertEqual(alias.destination, Url("www.google.com"))

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
        self.assertEqual(alias.destination, Url("www.google.com"))

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

        string = "[[Promise]](exclude)"
        self.assertRaises(ValueError, Alias.from_string, string)

        string = "\n".join(["[something]([[page with", "newline]])"])
        self.assertRaises(ValueError, Alias.from_string, string)

    def test_find_and_replace(self):
        a = Alias.find_and_replace("something [link]([[page [[in page]]]]) to [[something]] and a [france](www.google.com), [derp](((y3LFc4rFK)))")
        b = [
            String("something "), 
            Alias("link",PageRef.from_string("[[page [[in page]]]]")),
            String(" to [[something]] and a "), 
            Alias("france", Url("www.google.com")), 
            String(", "), 
            Alias("derp", BlockRef("y3LFc4rFK"))
        ]
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

        string = "```javascript\ndef foo(x+y):\n    return x+y```"
        cb = CodeBlock.from_string(string)
        self.assertEqual(cb.language, "javascript")
        self.assertEqual(cb.code, 'def foo(x+y):\n    return x+y')

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

        # Code block with back ticks inside
        string = "```javascript\nx = () => return `derp`\n```"
        language, code = "javascript", "x = () => return `derp`\n"
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
        b = "<pre><code>def foo(x+y):\n    return x+y</code></pre>"
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
        youtube = View.from_string("{{[[youtube]]:www.youtube.com}}")
        self.assertEqual(youtube.name, PageRef("youtube"))
        self.assertEqual(youtube.text, "www.youtube.com")

        query = View.from_string("{{[[query]]:{and:[[page]][[tag]]}}}")
        self.assertEqual(query.name, PageRef("query"))
        self.assertEqual(query.text, "{and:[[page]][[tag]]}")

        mentions = View.from_string("{{[[mentions]]:[[page]]}}")
        self.assertEqual(mentions.name, PageRef("mentions"))
        self.assertEqual(mentions.text, "[[page]]")

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
        a = View("query", "some text").to_string()
        b = "{{query:some text}}"
        self.assertEqual(a, b)

    def test_to_html(self):
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


class TestEmbed(unittest.TestCase):
    def test_from_string(self):
        embed = Embed.from_string("{{[[embed]]:((hh2wTNsMz))}}")
        self.assertEqual(embed.name, PageRef("embed"))
        self.assertEqual(embed.blockref, BlockRef("hh2wTNsMz"))

    def test_find_and_replace(self):
        string = "here's a {{embed: ((hh2wTNsMz))}}"
        a = Embed.find_and_replace(string)
        b = BlockContent([
            String("here's a "),
            Embed("embed", BlockRef("hh2wTNsMz"))
        ])
        self.assertListEqual(a,b)

    def to_string(self):
        a = Embed("embed", BlockRef("hh2wTNsMz")).to_string()
        b = "{{embed:((hh2wTNsMz))}}"
        self.assertEqual(a, b)


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

        a = PageRef.from_string("[[]]").title
        b = ""
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
            '<span class="rm-page-ref rm-page-ref-link-color">page</span>'\
            '<span class="rm-page-ref-brackets">]]</span></span>'
        self.assertEqual(a, b)
        a = PageRef("page").to_html()
        b = '<span data-link-title="page">'\
            '<span class="rm-page-ref-brackets">[[</span>'\
            '<span class="rm-page-ref rm-page-ref-link-color">page</span>'\
            '<span class="rm-page-ref-brackets">]]</span></span>'
        self.assertEqual(a, b)

    def test_get_tags(self):
        a = PageRef("[[page in a [[page]]]]ness").get_tags()
        b = ["[[page in a [[page]]]]ness","page in a [[page]]", "page"]
        self.assertSetEqual(set(a), set(b))

        tags = PageRef.from_string("[[]]").get_tags()
        self.assertEqual(tags, [])

    def test_extract_page_ref_strings(self):
        a = PageRef.extract_page_ref_strings("[[page]] and [[another]]")
        b = ["[[page]]", "[[another]]"]
        self.assertSetEqual(set(a), set(b))

        a = PageRef.extract_page_ref_strings("[[page]] and [not a ref]] then [[another]]")
        b = ["[[page]]", "[[another]]"]
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

        a = PageTag.from_string("#.ankify").title
        b = ".ankify"
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
        b = '<span data-tag="tag" class="rm-page-ref rm-page-ref-tag">#tag</span>'
        self.assertEqual(a, b)
        a = PageTag.from_string("#[[tag]]").to_html()
        b = '<span data-tag="tag" class="rm-page-ref rm-page-ref-tag">#tag</span>'
        self.assertEqual(a, b)
        a = PageTag.from_string("#[[[[tag]]:((cdYtyouxk))]]").to_html()
        b = '<span data-tag="[[tag]]:((cdYtyouxk))" class="rm-page-ref rm-page-ref-tag">#[[tag]]:((cdYtyouxk))</span>'
        self.assertEqual(a, b)
        a = PageTag.from_string("#[[[[source]]:[[some book]]]]").to_html()
        b = '<span data-tag="[[source]]:[[some book]]" class="rm-page-ref rm-page-ref-tag">#[[source]]:[[some book]]</span>'
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
            '<span class="rm-page-ref-brackets">[[</span><span '\
            'class="rm-page-ref rm-page-ref-link-color">page</span><span '\
            'class="rm-page-ref-brackets">]]</span></span> ref and a <span '\
            'data-tag="tag" class="rm-page-ref rm-page-ref-tag">'\
            '#tag</span></span></div>'
        self.assertEqual(a, b)

    def test_get_tags(self):
        a = BlockRef("LWGXbhfz_", self.roam_db).get_tags()
        b = []
        self.assertListEqual(a, b)


class TestUrl(unittest.TestCase):
    def test_from_string(self):
        url = "http://www.google.com"
        self.assertEqual(Url.from_string(url).to_string(), url)
        url = "www.google.com"
        self.assertEqual(Url.from_string(url).to_string(), url)

    def test_find_and_replace(self):
        string = "something with a link http://www.google.com and another www.foo.com/foo in #it"
        a = Url.find_and_replace(string)
        b = BlockContent([
            String("something with a link "), 
            Url("http://www.google.com"), 
            String(" and another "),
            Url("www.foo.com/foo"), 
            String(" in #it"), 
        ])
        self.assertListEqual(a, b)

    def test_to_html(self):
        a = Url("http://www.google.com").to_html()
        b = '<span><a href="http://www.google.com">http://www.google.com</a></span>'
        self.assertEqual(a, b)

        # add http to href
        a = Url("www.google.com").to_html()
        b = '<span><a href="http://www.google.com">www.google.com</a></span>'
        self.assertEqual(a, b)

    def test_pattern(self):
        should_match = [
            "www.foo.com",
            "www.foo.com/blah_blah",
            "http://foo.com/blah_blah",
            "http://foo.com/blah_blah/",
            "http://foo.com/blah_blah_(wikipedia)",
            "http://foo.com/blah_blah_(wikipedia)_(again)",
            "http://www.example.com/wpstyle/?p=364",
            "https://www.example.com/foo/?bar=baz&inga=42&quux",
            "http://userid:password@example.com:8080",
            "http://userid:password@example.com:8080/",
            "http://userid@example.com",
            "http://userid@example.com/",
            "http://userid@example.com:8080",
            "http://userid@example.com:8080/",
            "http://userid:password@example.com",
            "http://userid:password@example.com/",
            "http://142.42.1.1/",
            "http://142.42.1.1:8080/",
            "http://foo.com/blah_(wikipedia)#cite-1",
            "http://foo.com/blah_(wikipedia)_blah#cite-1",
            "http://foo.com/(something)?after=parens",
            "http://code.google.com/events/#&product=browser",
            "http://j.mp",
            "http://foo.bar/?q=Test%20URL-encoded%20stuff",
            "http://1337.net",
            "http://a.b-c.de",
            "http://223.255.255.254",
        ]
        should_not_match = [
            "http://",
            "http://.",
            "http://..",
            "http://../",
            "http://?",
            "http://??",
            "http://??/",
            "http://#",
            "http://##",
            "http://##/",
            "//",
            "//a",
            "///a",
            "///",
            "http:///a",
            "foo.com",
            "rdar://1234",
            "h://test",
            "http://",
            "shouldfail.com",
            "://",
            "should",
            "fail",
            "ftps://foo.bar/",
            "http://3628126748",
        ]
        pat = Url.create_pattern()
        for string in should_match:
            self.assertIsNotNone(re.match(pat, string))
        for string in should_not_match:
            self.assertIsNone(re.match(pat, string))


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
        b = '<span><strong>attribute:</strong></span>'
        self.assertEqual(a,b)

    def test_get_tags(self):
        a = Attribute("attr").get_tags()
        b = ["attr"]
        self.assertListEqual(a,b)


class TestEmphasis(unittest.TestCase):
    def test_all(self):
        string = '**something** `some code` and `more code` derp and __underlined_stuff__ and ^^highlights^^'
        html = BlockContent()._all_emphasis_to_html(string)
        expected = '<b>something</b> <code>some code</code> and <code>more code</code> derp and <em>underlined_stuff</em> and <span class="roam-highlight">highlights</span>'
        self.assertEqual(html, expected)

    def test_lots_of_emphasis(self):
        string = 'something `some code` and `more code` and `even more code`'
        html = BlockContent()._all_emphasis_to_html(string)
        expected = 'something <code>some code</code> and <code>more code</code> and <code>even more code</code>'
        self.assertEqual(html, expected)


if __name__=="__main__":
    unittest.main()
