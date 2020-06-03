import unittest 
from roam import Cloze 
import roam

class TestCloze(unittest.TestCase):
    def test_get_content(self):
        self.assertEqual(Cloze("{something}")._get_content(), "something")
        self.assertEqual(Cloze("{c1:something}")._get_content(), "something")
        self.assertEqual(Cloze("{c99:something}")._get_content(), "something")
        self.assertEqual(Cloze("{1:something}")._get_content(), "something")
        self.assertEqual(Cloze("{2|something}")._get_content(), "something")

    def test_get_id(self):
        self.assertEqual(Cloze("{something}")._get_id(), None)
        self.assertEqual(Cloze("{c1:something}")._get_id(), 1)
        self.assertEqual(Cloze("{c99:something}")._get_id(), 99)
        self.assertEqual(Cloze("{1:something}")._get_id(), 1)
        self.assertEqual(Cloze("{2|something}")._get_id(), 2)

    def test_test(self):
        self.assertListEqual([1,2,3], [1,2,3])

    def test_assign_cloze_ids(self):
        input = "{something} {which} totally {c3:has} a {c5:lot} of {1:clozes} {2|brah}"
        objects = Cloze.objectify(input)
        Cloze._assign_cloze_ids([o for o in objects if type(o)==Cloze])
        cloze_ids = [o.id for o in objects if type(o)==Cloze]
        self.assertListEqual(cloze_ids, [4,6,3,5,1,2])

    def test_format_clozes(self):
        input = "{something} {which} totally {c3:has} a {c5:lot} of {1:clozes} {2|brah}"
        output = "{c4:something} {c6:which} totally {c3:has} a {c5:lot} of {c1:clozes} {c2:brah}"
        self.assertEqual(Cloze.format_clozes(input), output)

    def test_uncloze_namespace(self):
        input = "{[[herp/derp/burp]]} is in the house"

        self.assertEqual(Cloze.format_clozes(input, uncloze_namespace=False), 
            "{c1:[[herp/derp/burp]]} is in the house")

        self.assertEqual(Cloze.format_clozes(input, uncloze_namespace=True), 
            "[[herp/derp/{c1:burp}]] is in the house")

    def test_ankify_clozes(self):
        input = "{c4:something} herp {c6:derp}"
        output = "{{c4::something}} herp {{c6::derp}}"
        self.assertEqual(Cloze.ankify_clozes(input), output)

    # TODO: this didn't cloze for some reason:
    # [[LMF]] stands for {Ladle Metallurgy Furnace} #anki_note
        

if __name__=="__main__":

    unittest.main()