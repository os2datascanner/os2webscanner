"""Unit-test util for tests os2webscanner.tests"""
# flake8: noqa pydocstyle:noqa
from os2datascanner.projects.admin.adminapp.models.organization_model import Organization
from os2datascanner.projects.admin.adminapp.models.scans.scan_model import Scan
from os2datascanner.projects.admin.adminapp.models.scans.webscan_model import WebScan


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


class CreateExchangeDomain(object):

    def create_exchangedomain(self):
        return ExchangeDomain.objects.create(
            url='@magenta.dk',
            organization=Organization.objects.get()
        )


class CreateExchangeScan(object):

    def create_exchangescan(self):
        return ExchangeScan.objects.create(
            status=Scan.DONE,
            mark_scan_as_done=True
        )


class CreateWebScan(object):

    def create_webscan(self):
        return WebScan.objects.create(
            status=Scan.DONE
        )


class CreateFileScan(object):

    def create_filescan(self):
        return FileScan.objects.create(
            status=Scan.DONE
        )
