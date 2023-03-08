from django.test import TestCase, Client
from LegacySite.models import Card
import json
import os
# Create your tests here.

class MyTest(TestCase):
    # Django's test run with an empty database. We can populate it with
    # data by using a fixture. You can create the fixture by running:
    #    mkdir LegacySite/fixtures
    #    python manage.py dumpdata LegacySite > LegacySite/fixtures/testdata.json
    # You can read more about fixtures here:
    #    https://docs.djangoproject.com/en/4.0/topics/testing/tools/#fixture-loading
    fixtures = ["testdata.json"]

    # Assuming that your database had at least one Card in it, this
    # test should pass.
    def test_get_card(self):
        allcards = Card.objects.all()
        self.assertNotEqual(len(allcards), 0)

    def test_xss(self):
        self.client = Client()
        payload = '<script>alert("hello")</script>' 
        encoded_payload = '&lt;script&gt;alert(&quot;hello&quot;)&lt;/script&gt;'
        self.client.login(username='test', password='test')    
        response_xss = self.client.get('/buy.html', {'director': payload})
        self.assertContains(response_xss, encoded_payload)

    def test_xsrf(self):
        self.client = Client(enforce_csrf_checks=True)
        resp_login = self.client.login(username='test', password='test')
        resp_xsrf = self.client.post('/gift/0', {'amount': '1', 'username': 'test2'})
        self.assertTrue(resp_login)
        self.assertEqual(resp_xsrf.status_code, 403)

    def test_sqli(self):
        self.client = Client()
        self.client.login(username='test', password='test')
        with open('part1/sqli.gftcrd') as giftcard:
            resp_sqli = self.client.post('/use.html',{'card_supplied': 'True', 'card_data': giftcard})
            self.assertEqual(resp_sqli.context.get('card_found', None), None)

    def test_cmdi(self):
        fname = ' & touch testFile.txt ; '
        self.client = Client()
        self.client.login(username='test', password='test')
        with open('part1/cmdiTest.gftcrd') as giftcard:
            try:
                resp_cmdi = self.client.post('/use.html',{'card_supplied': 'True', 'card_fname': fname, 'card_data': giftcard})
            except:
                pass    
            self.assertFalse(os.path.exists('testFile.txt'))