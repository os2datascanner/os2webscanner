"""Unit-test util for tests os2webscanner.tests"""
# flake8: noqa pydocstyle:noqa
from ..models.organization_model import Organization
from ..models.filedomain_model import FileDomain


class CreateOrganization(object):

    def create_organization(self):
        return Organization.objects.create(
            name='Magenta',
            contact_email='info@magenta.dk',
            contact_phone='39393939'
        )


class CreateFileDomain(object):

    def create_filedomain(self):
        return FileDomain.objects.create(
            url='/something/test',
            organization=Organization.objects.get()
        )
