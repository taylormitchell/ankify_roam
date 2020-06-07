import unittest 
import anki_connect
from roam import Attribute, Block, CodeBlock, View, Cloze, Alias, Checkbox, Button, PageRef, PageTag, BlockRef, Url, Image, String, RoamObjectList 
import roam

# TODO: all RoamObject types should implement the interface

#class TestExample(unittest.TestCase):
#    def test_to_string(self):
#        self.assertEqual()
#
#    def test_to_html(self):
#        self.assertEqual()
#        
#    def test_get_tags(self):
#        self.assertEqual()
#
#    def test_validate_string(self):
#        self.assertTrue()
#        self.assertFalse()
#
#    def test_find_and_replace(self):
#        self.assertEqual()


class TestRoamObjectList(unittest.TestCase):
    def test_find_and_replace(self):
        """
        Roam Object Coverage
        Cloze: 
        Image:
        Alias: 1,
        CodeBlock: 
        Checkbox: 1,
        View:
        Button:
        PageRef: 1,
        PageTag: 1,
        BlockRef: 1,
        """
        # Test 1 
        string = "{{[[TODO]]}} something [this]([[This]]) [[Saturday]] about ((ZtmwW4k32)) #Important"
        a = RoamObjectList.from_string(string)
        b = RoamObjectList([
            Checkbox(False),
            String(" something "),
            Alias("this",PageRef("This")),
            String(" "),
            PageRef("Saturday"),
            String(" about "),
            BlockRef("ZtmwW4k32"),
            String(" "),
            PageTag("#Important")
        ])
        self.assertListEqual(a, b)
        tags = ["TODO","This","Saturday","Important"]
        self.assertSetEqual(set(a.get_tags()), set(tags))


    def test_get_tags(self):
        string = "Something with [[page refs]] and #some #[[tags]]"
        tags = sorted(RoamObjectList.from_string(string).get_tags())
        self.assertListEqual(tags, ["page refs","some","tags"])


class TestCloze(unittest.TestCase):
    def setUp(self):
        self.maxDiff = 1000

    def test_get_content(self):
        self.assertEqual(Cloze._get_text("{something}"), "something")
        self.assertEqual(Cloze._get_text("{c1:something}"), "something")
        self.assertEqual(Cloze._get_text("{c99:something}"), "something")
        self.assertEqual(Cloze._get_text("{1:something}"), "something")
        self.assertEqual(Cloze._get_text("{2|something}"), "something")

    def test_get_id(self):
        self.assertEqual(Cloze._get_id("{something}"), None)
        self.assertEqual(Cloze._get_id("{c1:something}"), 1)
        self.assertEqual(Cloze._get_id("{c99:something}"), 99)
        self.assertEqual(Cloze._get_id("{1:something}"), 1)
        self.assertEqual(Cloze._get_id("{2|something}"), 2)

    def test_assign_cloze_ids(self):
        clozes = [Cloze(None, "no id"), Cloze(6, "has id"), Cloze(1, "has id"), 
                  Cloze(None, "no id"), Cloze(3, "also has id")]
        Cloze._assign_cloze_ids(clozes)
        cloze_ids = [c.id for c in clozes]
        self.assertListEqual(cloze_ids, [2,6,1,4,3])

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

    def test_get_tags(self):
        cloze = Cloze(1, "Something with [[page refs]] and #some #[[tags]]")
        self.assertListEqual(sorted(cloze.get_tags()), ["page refs","some","tags"])

    def test_validate_string(self):
        string = "{text}"
        self.assertTrue(Cloze.validate_string(string))
        string = "{1:text}"
        self.assertTrue(Cloze.validate_string(string))
        string = "{c1:text}"
        self.assertTrue(Cloze.validate_string(string))
        string = "{c1|text}"
        self.assertTrue(Cloze.validate_string(string))
        string = "text"
        self.assertFalse(Cloze.validate_string(string))
        string = "{text} and {more text}"
        self.assertFalse(Cloze.validate_string(string))
        string = "{{button}}"
        self.assertFalse(Cloze.validate_string(string))

    def test_find_and_replace(self):
        a = Cloze.find_and_replace("Something with a {cloze}")
        b = [String("Something with a "), Cloze(1, "cloze")]
        self.assertListEqual(a, b)


class TestImage(unittest.TestCase):
    def test_validate_string(self):
        string = "![alt](https://firebasestorage.googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2Fsecond_brain%2Feih7AcCzD1.png?alt=media&token=12eae516-db41-4fbf-907c-4e0f8eec5840)"
        self.assertTrue(Image.validate_string(string))
        string = "[alt](https://google.com)"
        self.assertFalse(Image.validate_string(string))

    def test_parse_url(self):
        string = "![alt](https://firebasestorage.googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2Fsecond_brain%2Feih7AcCzD1.png?alt=media&token=12eae516-db41-4fbf-907c-4e0f8eec5840)"
        image = Image.from_string(string)
        src = "https://firebasestorage.googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2Fsecond_brain%2Feih7AcCzD1.png?alt=media&token=12eae516-db41-4fbf-907c-4e0f8eec5840"
        alt = "alt"
        self.assertEqual(image.src, src)
        self.assertEqual(image.alt, alt)

    def test_to_html(self):
        a = Image("https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png", "alt").to_html()
        b = '<img src="https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png" alt="alt" draggable="false" class="rm-inline-img">'
        self.assertEqual(a, b)


class TestAlias(unittest.TestCase):
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
        class RoamDbProxy:
            def get_block_by_uid(self, uid):
                return Block.from_string("{{[[TODO]]}} some block with a [[page]] ref and a #tag")
        a = Alias("text", BlockRef("y3LFc4rFK", roam_db=RoamDbProxy())).to_html()
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

    def test_validate_string(self):
        string = "[something](www.google.com)"
        self.assertTrue(Alias.validate_string(string))

        string = "[something]([[page]])"
        self.assertTrue(Alias.validate_string(string))

        string = "[something](((LtKPM-UZe)))"
        self.assertTrue(Alias.validate_string(string))

        string = "[something](((LtKPM- UZe)))"
        self.assertFalse(Alias.validate_string(string))

        string = "[](www.google.com)"
        self.assertFalse(Alias.validate_string(string))

        string = "[something[]](www.google.com)"
        self.assertFalse(Alias.validate_string(string))

        string = "[something]()"
        self.assertFalse(Alias.validate_string(string))

        string = "[something](www.google.com[)"
        self.assertFalse(Alias.validate_string(string))

        string = "[something](www.google.com) and something)"
        self.assertFalse(Alias.validate_string(string))

    def test_find_and_replace(self):
        a = Alias.find_and_replace("something [link]([[page]]) to something")
        b = [String("something "),Alias("link",PageRef("page")),String(" to something")]
        self.assertListEqual(a, b)


class TestCodeBlock(unittest.TestCase):
    def test_init(self):
        string = "```clojure\ndef foo(x+y):\n    return x+y```"
        language = 'clojure'
        code = 'def foo(x+y):\n    return x+y'
        cb = CodeBlock.from_string(string)
        self.assertEqual(cb.language, language)
        self.assertEqual(cb.code, code)

        string = "```\ndef foo(x+y):\n    return x+y```"
        language = None
        code = 'def foo(x+y):\n    return x+y'
        cb = CodeBlock.from_string(string)
        self.assertEqual(cb.language, language)
        self.assertEqual(cb.code, code)

    def test_find_and_replace(self):
        string = "something something ```clojure\ndef foo(x+y):\n    return x+y```"
        a = CodeBlock.find_and_replace(string)
        b = RoamObjectList([
                String("something something "), 
                CodeBlock('def foo(x+y):\n    return x+y',"clojure")])
        self.assertListEqual(a, b)


    def test_to_html(self):
        a = CodeBlock("def foo(x+y):\n    return x+y", "clojure").to_html()
        b = "<pre>def foo(x+y):<br>    return x+y</pre>"
        self.assertEqual(a, b)


class TestCheckbox(unittest.TestCase):
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

    def test_validate_string(self):
        string = "{{[[TODO]]}}"
        self.assertTrue(Checkbox.validate_string(string))
        string = "{{[[DONE]]}}"
        self.assertTrue(Checkbox.validate_string(string))
        string = "{{[[TODO]]}} some text"
        self.assertFalse(Checkbox.validate_string(string))
        string = "{{TODO}}"
        self.assertFalse(Checkbox.validate_string(string))

    def test_find_and_replace(self):
        roam_objects = RoamObjectList.from_string("{{[[TODO]]}} thing to do")
        a = Checkbox.find_and_replace(roam_objects)
        b = [Checkbox(checked=False), String(" thing to do")]
        self.assertListEqual(a, b)


class TestView(unittest.TestCase):
    def test_find_and_replace(self):
        string = "here's a {{query: {and:[[page]]}}}"
        a = View.find_and_replace(string)
        b = RoamObjectList([
            String("here's a "),
            View("query"," {and:[[page]]}")
        ])
        self.assertListEqual(a,b)

    def test_from_string(self):
        embed = View.from_string("{{[[embed]]:((hh2wTNsMz))}}")
        self.assertEqual(embed.type, "embed")
        self.assertEqual(embed.text, "((hh2wTNsMz))")

        youtube = View.from_string("{{[[youtube]]:www.youtube.com}}")
        self.assertEqual(youtube.type, "youtube")
        self.assertEqual(youtube.text, "www.youtube.com")

        query = View.from_string("{{[[query]]:{and:[[page]][[tag]]}}}")
        self.assertEqual(query.type, "query")
        self.assertEqual(query.text, "{and:[[page]][[tag]]}")

        mentions = View.from_string("{{[[mentions]]:[[page]]}}")
        self.assertEqual(mentions.type, "mentions")
        self.assertEqual(mentions.text, "[[page]]")

        embed = View.from_string("{{embed:((hh2wTNsMz))}}")
        self.assertEqual(embed.type, "embed")
        self.assertEqual(embed.text, "((hh2wTNsMz))")

        youtube = View.from_string("{{youtube:www.youtube.com}}")
        self.assertEqual(youtube.type, "youtube")
        self.assertEqual(youtube.text, "www.youtube.com")

        query = View.from_string("{{query:{and:[[page]][[tag]]}}}")
        self.assertEqual(query.type, "query")
        self.assertEqual(query.text, "{and:[[page]][[tag]]}")

        mentions = View.from_string("{{mentions:[[page]]}}")
        self.assertEqual(mentions.type, "mentions")
        self.assertEqual(mentions.text, "[[page]]")

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


class TestButton(unittest.TestCase):
    def test_find_and_replace(self):
        string = "here's a {{Button}} and {{another: with stuff}}"
        a = Button.find_and_replace(string)
        b = RoamObjectList([
            String("here's a "),
            Button("Button"),
            String(" and "),
            Button("another", " with stuff"),
        ])
        self.assertListEqual(a,b)

    def test_validate_string(self):
        string = "{{text}}"
        self.assertTrue(Button.validate_string(string))
        string = "{{text: with more text}}"
        self.assertTrue(Button.validate_string(string))

    def to_html(self):
        a = Button("name")
        b = '<button class="bp3-button bp3-small dont-focus-block">name</button>'
        self.assertEqual(a, b)
        a = Button("name", "with some other name")
        b = '<button class="bp3-button bp3-small dont-focus-block">name</button>'
        self.assertEqual(a, b)


class TestPageRef(unittest.TestCase):
    def test_find_and_replace(self):
        string = "something with a [[couple]] of [[pages]] in it"
        a = PageRef.find_and_replace(string)
        b = RoamObjectList([
            String("something with a "), 
            PageRef("couple"), 
            String(" of "), 
            PageRef("pages"), 
            String(" in it")
        ])
        self.assertListEqual(a, b)

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


class TestPageTag(unittest.TestCase):
    def test_find_and_replace(self):
        string = "something with [[some]] #[[tags]] in #it"
        a = PageTag.find_and_replace(string)
        b = RoamObjectList([
            String("something with [[some]] "), 
            PageTag("#[[tags]]"), 
            String(" in "), 
            PageTag("#it"), 
        ])
        self.assertListEqual(a, b)

    def test_to_html(self):
        a = PageTag("#tag").to_html()
        b = '<span tabindex="-1" data-tag="tag" class="rm-page-ref rm-page-ref-tag">#tag</span>'
        self.assertEqual(a, b)
        a = PageTag("#[[tag]]").to_html()
        b = '<span tabindex="-1" data-tag="tag" class="rm-page-ref rm-page-ref-tag">#tag</span>'
        self.assertEqual(a, b)
        a = PageTag("#[[[[tag]]:((cdYtyouxk))]]").to_html()
        b = '<span tabindex="-1" data-tag="[[tag]]:((cdYtyouxk))" class="rm-page-ref rm-page-ref-tag">#[[tag]]:((cdYtyouxk))</span>'
        self.assertEqual(a, b)


class TestBlockRef(unittest.TestCase):
    def setUp(self):
        class RoamDbProxy:
            def get_block_by_uid(self, uid):
                blocks = {
                    "mZPhN5wFj": Block.from_string("some block"),
                    "LWGXbhfz_": Block.from_string("{{[[TODO]]}} some block with a [[page]] ref and a #tag") 
                }
                return blocks[uid]
        self.roam_db = RoamDbProxy()

    def test_find_and_replace(self):
        string = "something with a ((4MxiXZn9f)) in #it"
        a = BlockRef.find_and_replace(string)
        b = RoamObjectList([
            String("something with a "), 
            BlockRef("4MxiXZn9f"), 
            String(" in #it"), 
        ])
        self.assertListEqual(a, b)

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


class TestUrl(unittest.TestCase):
    def test_to_html(self):
        a = Url("http://www.google.com").to_html()
        b = '<span><a href="http://www.google.com">http://www.google.com</a></span>'
        self.assertEqual(a, b)


class TestAttribute(unittest.TestCase):
    def test_find_and_replace(self):
        string = "attribute:: text"
        a = Attribute.find_and_replace(string)
        b = RoamObjectList([Attribute("attribute"), String(" text")])
        self.assertListEqual(a,b)

        string = "attribute:::: text"
        a = Attribute.find_and_replace(string)
        b = RoamObjectList([Attribute("attribute"), String(":: text")])
        self.assertListEqual(a,b)

if __name__=="__main__":
    unittest.main()
