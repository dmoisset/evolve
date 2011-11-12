from django.test import TestCase
from evolve.rules import models

class ScoreTest(TestCase):

    def setUp(self):
        self.score = models.Score.new()

    def test_correct_count(self):
        self.assertEqual(len(self.score), 7)

    def test_correct_values(self):
        self.assertTrue(all(value==0 for value in self.score))
        
    def test_set_attributes(self):
        """Tests setting the 7 relevant attributes with _replace() """
        score = self.score._replace(treasury=1, military=2, special=3, civilian=4)
        score = score._replace(economy=5, science=6, personality=7)
        self.assertEqual(score, (1,2,3,4,5,6,7))
    
    def test_add(self):
        s2 = models.Score(1,3,5,7,2,4,6)
        s3 = models.Score(3,3,3,3,3,3,3)
        result = self.score + s2 + s3
        self.assertEqual(result, (4,6,8,10,5,7,9))


    def test_total(self):
        s = models.Score(4,6,8,10,5,7,9)
        result = s.total()
        self.assertEqual(result, 49)

class BuildingKindTest(TestCase):

    def test_unicode(self):
        bk = models.BuildingKind(name=models.PERSONALITY)
        self.assertNotEqual(unicode(bk), '')

class ResourceTest(TestCase):

    def test_unicode(self):
        r = models.Resource(name=u'Test Resource')
        self.assertEqual(unicode(r), u'Test Resource')


class ScienceTest(TestCase):

    def test_unicode(self):
        s = models.Science(name=u'Test Science')
        self.assertEqual(unicode(s), u'Test Science')

class VariantTest(TestCase):

    def test_unicode(self):
        s = models.Variant(label=u'Test Variant')
        self.assertEqual(unicode(s), u'Test Variant')

class AgeTest(TestCase):

    def setUp(self):
        self.a1 = models.Age.objects.create(
            name='test age 1',
            order=0,
            direction='l',
            victory_score=1
        )
        self.a2 = models.Age.objects.create(
            name='test age 2',
            order=1,
            direction='l',
            victory_score=1
        )

    def test_first(self):
        first_age = models.Age.first()
        self.assertEqual(first_age, self.a1)

    def test_next(self):
        next_age = self.a1.next()
        self.assertEqual(next_age, self.a2)
    
    def test_next_after_final(self):
        next_age = self.a2.next()
        self.assertIs(next_age, None)
    
    def test_unicode(self):
        self.assertEqual(unicode(self.a1), u'test age 1')

