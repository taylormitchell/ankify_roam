import unittest 
import anki_connect
from roam import Cloze, Alias, Curly, PageRef, PageTag, BlockRef, URL, Image, RoamObjectList 
import roam

# TODO: all RoamObject types should implement the interface


class TestRoamObjectList(unittest.TestCase):
    def test_to_html(self):
        string = "Something with a {cloze}"
        roam_objects = RoamObjectList.from_string(string)
        self.assertEqual(roam_objects.to_html(), "Something with a {{c1::cloze}}")
#
#
#class TestAlias(unittest.TestCase):
#    def test_validate_string(self):
#        string = "[something](www.google.com)"
#        self.assertTrue(Alias.validate_string(string))
#
#        string = "[something]([[page]])"
#        self.assertTrue(Alias.validate_string(string))
#
#        string = "[something](((LtKPM-UZe)))"
#        self.assertTrue(Alias.validate_string(string))
#
#        string = "[](www.google.com)"
#        self.assertFalse(Alias.validate_string(string))
#
#        string = "[something[]](www.google.com)"
#        self.assertFalse(Alias.validate_string(string))
#
#        string = "[something]()"
#        self.assertFalse(Alias.validate_string(string))
#
#        string = "[something](www.google.com[)"
#        self.assertFalse(Alias.validate_string(string))
#
#        string = "[something](www.google.com) and something)"
#        self.assertFalse(Alias.validate_string(string))
#
#
#class TestCurly(unittest.TestCase):
#    def test_validate_string(self):
#        string = "{{text}}"
#        self.assertTrue(Curly.validate_string(string))
#
#
#class TestImage(unittest.TestCase):
#    def test_parse_url(self):
#        image_md = "![](https://firebasestorage.googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2Fsecond_brain%2Feih7AcCzD1.png?alt=media&token=12eae516-db41-4fbf-907c-4e0f8eec5840)"
#        url = "https://firebasestorage.googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2Fsecond_brain%2Feih7AcCzD1.png?alt=media&token=12eae516-db41-4fbf-907c-4e0f8eec5840"
#        self.assertEqual(Image(image_md).url, url)
#
#    def test_to_html(self):
#        image_md = "![](https://firebasestorage.googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2Fsecond_brain%2Feih7AcCzD1.png?alt=media&token=12eae516-db41-4fbf-907c-4e0f8eec5840)"
#        image_html = '<img src="https://firebasestorage.googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2Fsecond_brain%2Feih7AcCzD1.png?alt=media&token=12eae516-db41-4fbf-907c-4e0f8eec5840">'
#        self.assertEqual(Image(image_md).to_html(), image_html)
#
#
#class TestCloze(unittest.TestCase):
#    def test_get_content(self):
#        self.assertEqual(Cloze("{something}")._get_content(), "something")
#        self.assertEqual(Cloze("{c1:something}")._get_content(), "something")
#        self.assertEqual(Cloze("{c99:something}")._get_content(), "something")
#        self.assertEqual(Cloze("{1:something}")._get_content(), "something")
#        self.assertEqual(Cloze("{2|something}")._get_content(), "something")
#
#    def test_get_id(self):
#        self.assertEqual(Cloze("{something}")._get_id(), None)
#        self.assertEqual(Cloze("{c1:something}")._get_id(), 1)
#        self.assertEqual(Cloze("{c99:something}")._get_id(), 99)
#        self.assertEqual(Cloze("{1:something}")._get_id(), 1)
#        self.assertEqual(Cloze("{2|something}")._get_id(), 2)
#
#    def test_test(self):
#        self.assertListEqual([1,2,3], [1,2,3])
#
#    def test_assign_cloze_ids(self):
#        input = "{something} {which} totally {c3:has} a {c5:lot} of {1:clozes} {2|brah}"
#        objects = Cloze.objectify(input)
#        Cloze._assign_cloze_ids([o for o in objects if type(o)==Cloze])
#        cloze_ids = [o.id for o in objects if type(o)==Cloze]
#        self.assertListEqual(cloze_ids, [4,6,3,5,1,2])
#
#    def test_format_clozes(self):
#        input = "{something} {which} totally {c3:has} a {c5:lot} of {1:clozes} {2|brah}"
#        output = "{c4:something} {c6:which} totally {c3:has} a {c5:lot} of {c1:clozes} {c2:brah}"
#        self.assertEqual(Cloze.format_clozes(input), output)
#
#    def test_uncloze_namespace(self):
#        input = "{[[herp/derp/burp]]} is in the house"
#
#        self.assertEqual(Cloze.format_clozes(input, uncloze_namespace=False), 
#            "{c1:[[herp/derp/burp]]} is in the house")
#
#        self.assertEqual(Cloze.format_clozes(input, uncloze_namespace=True), 
#            "[[herp/derp/{c1:burp}]] is in the house")
#
#    def test_ankify_clozes(self):
#        input = "{c4:something} herp {c6:derp}"
#        output = "{{c4::something}} herp {{c6::derp}}"
#        self.assertEqual(Cloze.ankify_clozes(input), output)
#
#    def test_doesnt_match_double_bracket(self):
#        input = "don't match {{this}}"
#        self.assertEqual(Cloze.find_and_replace(input).to_string(), input)
#
#    def test_encloze(self):
#        self.assertEqual(Cloze.encloze(1,"string"), "{{c1::string}}")
#
#    # TODO: this didn't cloze for some reason:
#    # [[LMF]] stands for {Ladle Metallurgy Furnace} #anki_note
#    # [[Steel]] is {an alloy} mainly of {[[Iron]] and [[Carbon]]} #anki_note
#    # [[Steel]] is {an [alloy]([[Alloy]])} mainly of {[[Iron]] and [[Carbon]]} #anki_note"
#        

if __name__=="__main__":
    #string = "{[[something/which]]} and [some](www.google.com) other stuff"
    #roam_objects = RoamObjectList.from_string(string)
    #print(roam_objects.to_html())
    #string = "{something} {which} totally {{c3:has}} a {c5:lot} of {1:clozes} {2|brah}"
    #objects = Cloze.find_and_replace(string)
    #print(objects)

    unittest.main()
