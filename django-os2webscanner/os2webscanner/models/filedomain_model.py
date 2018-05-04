# -*- coding: UTF-8 -*-
# encoding: utf-8
# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )
import shlex
import logging

from subprocess import check_call, CalledProcessError

from django.conf import settings
from django.db import models

from os2webscanner.aescipher import decrypt
from .domain_model import Domain

# Get an instance of a logger
logger = logging.getLogger(__name__)


class FileDomain(Domain):

    """Represents a file domain to be scanned."""

    mountname = models.CharField(max_length=2048, verbose_name='Folder navn', null=True)

    # Run error messages
    MOUNT_FAILED = (
        "Scanneren kunne ikke startes," +
        " fordi netværksdrev ikke kunne monteres"
    )

    @property
    def root_url(self):
        """Return the root url of the domain."""
        url = self.url.replace('*.', '')
        """if (
                    not self.url.startswith('file://') and not
                self.url.startswith('file:///')
        ):
            return 'file://%s/' % url
        else:"""
        return url

    @property
    def generate_mountname(self):
        if not self.mountname:
            try:
                self.mountname = self.root_url.split('/')[0]
            except IndexError:
                self.mountname = self.root_url
            finally:
                self.save()

        return self.mountname

    @property
    def mount_url(self):
        return settings.NETWORKDRIVE_TMP_PREFIX + self.generate_mountname

    def smbmount(self):
        # TODO : Check if already mounted
        # Consider when to unmount. If two scanners are created for the same file domain,
        # who is then responsible for handling unmount.

        # What if folder is unmounted during scan??
        if self.authentication:
            import pdb; pdb.set_trace()
            password = decrypt(bytes(self.authentication.iv), bytes(self.authentication.ciphertext))
            command = 'mount -t cifs' + self.root_url + ' ' + self.mount_url + '-o username=' + self.authentication.username + ',password=' + password
            try:
                check_call(shlex.split(command), shell=True)
            except CalledProcessError as cpe:
                logger.error('Error occured while mounting drive: %s', self.root_url)
                logger.error('Error message %s', cpe)
                return self.MOUNT_FAILED

            return True

    def __str__(self):
        """Return the URL for the domain."""
        return self.url

    class Meta:
        db_table = 'os2webscanner_filedomain'
