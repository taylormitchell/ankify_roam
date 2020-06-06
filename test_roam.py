import unittest 
import anki_connect
from roam import Cloze, Alias, Checkbox, Button, PageRef, PageTag, BlockRef, URL, Image, String, RoamObjectList 
import roam

# TODO: all RoamObject types should implement the interface


class TestRoamObjectList(unittest.TestCase):
    def test_get_tags(self):
        string = "Something with [[page refs]] and #some #[[tags]]"
        tags = sorted(RoamObjectList.from_string(string).get_tags())
        self.assertListEqual(tags, ["page refs","some","tags"])

class TestCloze(unittest.TestCase):
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
            '<span class="rm-page-ref-brackets">[[</span>'\
            '<span class="rm-page-ref-link-color">page</span>'\
            '<span class="rm-page-ref-brackets">]]</span>'\
            '}}'
        self.assertEqual(a, b)
        a = Cloze(1,"[[page]]").to_html(pageref_cloze="inside")
        b = \
            '<span class="rm-page-ref-brackets">[[</span>'\
            '<span class="rm-page-ref-link-color">{{c1::page}}</span>'\
            '<span class="rm-page-ref-brackets">]]</span>'
        self.assertEqual(a, b)
        a = Cloze(1,"[[namespace/base]]").to_html(pageref_cloze="base_only")
        b = \
            '<span class="rm-page-ref-brackets">[[</span>'\
            '<span class="rm-page-ref-link-color">namespace/{{c1::base}}</span>'\
            '<span class="rm-page-ref-brackets">]]</span>'
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
        roam_objects = RoamObjectList.from_string("Something with a {cloze}")
        a = Cloze.find_and_replace(roam_objects)
        b = [String("Something with a "), Cloze(1, "cloze")]
        self.assertListEqual(a, b)

class TestCheckbox(unittest.TestCase):
    def test_to_string(self):
        self.assertEqual(Checkbox(True).to_string(), "{{[[DONE]]}}")
        self.assertEqual(Checkbox(False).to_string(), "{{[[TODO]]}}")

    def test_to_html(self):
        checkbox = Checkbox.from_string("{{[[TODO]]}}")
        a = checkbox.to_html()
        b = '<label class="check-container"><input type="checkbox"><span class="checkmark"></span></label>'
        self.assertEqual(a, b)
        checkbox = Checkbox.from_string("{{[[DONE]]}}")
        a = checkbox.to_html()
        b = '<label class="check-container"><input type="checkbox" checked=""><span class="checkmark"></span></label>'
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


class TestAlias(unittest.TestCase):
    def test_validate_string(self):
        string = "[something](www.google.com)"
        self.assertTrue(Alias.validate_string(string))

        string = "[something]([[page]])"
        self.assertTrue(Alias.validate_string(string))

        string = "[something](((LtKPM-UZe)))"
        self.assertTrue(Alias.validate_string(string))

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


class TestButton(unittest.TestCase):
    def test_validate_string(self):
        string = "{{text}}"
        self.assertTrue(Button.validate_string(string))


class TestImage(unittest.TestCase):
    def test_parse_url(self):
        image_md = "![](https://firebasestorage.googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2Fsecond_brain%2Feih7AcCzD1.png?alt=media&token=12eae516-db41-4fbf-907c-4e0f8eec5840)"
        url = "https://firebasestorage.googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2Fsecond_brain%2Feih7AcCzD1.png?alt=media&token=12eae516-db41-4fbf-907c-4e0f8eec5840"
        self.assertEqual(Image(image_md).url, url)

    def test_to_html(self):
        image_md = "![](https://firebasestorage.googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2Fsecond_brain%2Feih7AcCzD1.png?alt=media&token=12eae516-db41-4fbf-907c-4e0f8eec5840)"
        image_html = '<img src="https://firebasestorage.googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2Fsecond_brain%2Feih7AcCzD1.png?alt=media&token=12eae516-db41-4fbf-907c-4e0f8eec5840">'
        self.assertEqual(Image(image_md).to_html(), image_html)




if __name__=="__main__":
    #string = "{[[something/which]]} and [some](www.google.com) other stuff"
    #roam_objects = RoamObjectList.from_string(string)
    #print(roam_objects.to_html())
    #string = "{something} {which} totally {{c3:has}} a {c5:lot} of {1:clozes} {2|brah}"
    #objects = Cloze.find_and_replace(string)
    #print(objects)

    unittest.main()
