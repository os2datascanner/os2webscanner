import unittest

from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory

from .util import CreateOrganization


@unittest.skip("File domain is gone!")
class FileDomainTest(TestCase):
    """Unit-tests for the Create File Domain Form."""

    fields = [
        ["url"],
        ["organization"],
        ["username"],
        ["password"],
        ["validation_status"],
        ["exclusion_rules"]
    ]

    def setUp(self):
        self.factory = RequestFactory()
        CreateOrganization.create_organization(self)
        self.user = User.objects.create_user(
            username='jacob', email='jacob@magenta.dk', password='top_secret')
        # use models.userprofile_model

    def test_view_filedomains(self):
        self.client.login(username='jacob', password='top_secret')
        response = self.client.get('/filedomains/', follow=True)
        self.assertEqual(response.status_code, 200)

    def test_filedomain_inheritance(self):
        filedomain = CreateFileDomain.create_filedomain(self)
        domain = Domain.objects.get()
        domain = domain.filedomain
        self.assertEqual(filedomain.url, domain.url)
        self.assertEqual(isinstance(domain, FileDomain), True)

    """def test_create_filedomains(self):
        self.client.login(username='jacob', password='top_secret')
        form_data = {
            'url': 'something.test',
            'organization': 'magenta',
            'username': 'mette',
            'password': 'projektleder',
            'validation_status': '',
            'exclusion_rules': ''
        }
        response = self.client.post('/filedomains/add/', form_data, follow=True)
        self.assertEqual(response.status_code, 200)"""
