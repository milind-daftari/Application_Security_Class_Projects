import io
from django.db import IntegrityError
from django.test import TestCase, Client
from django.contrib.auth.models import User
from LegacySite.models import Card, User
from LegacySite.views import login_view, logout_view, buy_card_view, gift_card_view, use_card_view
import os
from . import extras
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
        with open('part1/sqli.gftcrd','rb') as giftcard:
            resp_sqli = self.client.post('/use.html',{'card_supplied': 'True', 'card_data': giftcard})
            assert b'Error 400: Invalid Card' in resp_sqli.content

    def test_cmdi(self):
        fname = ' & touch testFile.txt ; '
        self.client = Client()
        self.client.login(username='test', password='test')
        with open('part1/cmdiTest.gftcrd','rb') as giftcard:
            try:
                resp_cmdi = self.client.post('/use.html',{'card_supplied': 'True', 'card_fname': fname, 'card_data': giftcard})
            except:
                pass    
            self.assertFalse(os.path.exists('testFile.txt'))

    # Functionality tests: After adding encryption

    def test_login(self):
        self.client = Client()
        resp_login = self.client.login(username='test', password='test')
        self.assertEqual(resp_login, True)
    
    def test_logout(self):
        self.client = Client()
        resp_login = self.client.login(username='test', password='test')
        resp_rqst1 = self.client.get('/index.html')
        self.assertContains(resp_rqst1, "Sign Out")
        self.client.logout()
        resp_rqst2 = self.client.get('/index.html')
        self.assertContains(resp_rqst2, "Sign In")
    
    def test_buy(self):
        self.client = Client()
        self.client.login(username="test", password="test")
        resp_buy = self.client.post('/buy/1', data={'amount': '10'})
        self.assertEqual(resp_buy.status_code, 200)
        self.assertTrue(resp_buy['Content-Disposition'].startswith("attachment; filename=newcard.gftcrd"))

    def test_gift(self):
        self.client = Client()
        self.client.login(username="test", password="test")
        resp_gift = self.client.post('/gift/1', data={'username': 'test2', 'amount': '10'})
        self.assertEqual(resp_gift.status_code, 200)
        self.assertContains(resp_gift, "test2")

    def test_use_valid(self):
        self.client = Client()
        self.client.login(username="test", password="test")
        with open('part2/valid_test_card.gftcrd','rb') as giftcard:
            resp_use = self.client.post('/use',{'card_supplied': 'True', 'card_data': giftcard})
            self.assertContains(resp_use, "Card used!")

    def test_use_reuse(self):
        self.client = Client()
        self.client.login(username="test", password="test")
        with open('part2/used_test_card.gftcrd','rb') as giftcard1:
            resp_use = self.client.post('/use', {'card_supplied': 'True', 'card_data': giftcard1})
        try:
            with open('part2/used_test_card.gftcrd','rb') as giftcard2:
                resp_reuse = self.client.post('/use', {'card_supplied': 'True', 'card_data': giftcard2})
        except IntegrityError:
            self.assertTrue(True)


    def test_encryption_decryption(self):
        input_to_encrypt = "This is a test input."
        encrypted_data = extras.encrypt_card_file_data(input_to_encrypt)
        decrypted_data = extras.decrypt_card_file_data(encrypted_data)
        self.assertEqual(input_to_encrypt, decrypted_data)
    
    def test_buy_and_use(self):
        client = Client()
        client.login(username="test", password="test")
        user = User.objects.get(username="test")
        response = client.post('/buy/4', {'amount': 1337})
        self.assertEqual(response.status_code, 200)
        # Get the card that was returned
        card = Card.objects.filter(user=user.pk).order_by('-id')[0]
        card_data = response.content
        response = client.post('/use.html',
            {
                'card_supplied': 'True',
                'card_fname': 'Test',
                'card_data': io.BytesIO(card_data),
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Card used!', response.content)
        self.assertTrue(Card.objects.get(pk=card.id).used)
    
