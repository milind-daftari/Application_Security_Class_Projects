from django.test import TestCase, Client
from LegacySite.models import Card
from LegacySite.extras import parse_card_data
import json
from shlex import quote
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
        payload = '<script>alert("hello")</script>' 
        encoded_payload = '&lt;script&gt;alert(&quot;hello&quot;)&lt;/script&gt;'    
        response_xss = self.client.get('/buy.html', {'director': payload})
        self.assertContains(response_xss, encoded_payload)

    def test_xsrf(self):
        self.client = Client(enforce_csrf_checks=True)
        resp_xsrf = self.client.post('/gift/0', {'amount': '1', 'username': 'test2'})
        self.assertEqual(resp_xsrf.status_code, 403)

    def test_sqli(self):
        giftcard = open('part1/sqli.gftcrd')
        giftcard_path = f'./tmp/sqli.gftcrd'
        parsed_data = parse_card_data(giftcard.read(), giftcard_path)

        signature = json.loads(parsed_data)['records'][0]['signature']
        card_query = Card.objects.raw('select id from LegacySite_card where data = %s', [signature])

        self.assertEqual(len(card_query), 0)

    def test_cmdi(self):
        filename = '  & echo "hello" ; '
        input_command = 'echo 1' + filename
        quoted_input_command = quote(input_command)
        self.assertNotEqual(quoted_input_command, input_command)