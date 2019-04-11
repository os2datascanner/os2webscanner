# -*- coding: utf-8 -*-
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
import os
import logging
import tempfile
from subprocess import call, CalledProcessError

from django.conf import settings
from django.db import models

from .domain_model import Domain

# Get an instance of a logger
logger = logging.getLogger(__name__)


class FileDomain(Domain):

    """Represents a file domain to be scanned."""

    mountpath = models.CharField(max_length=2048, verbose_name='Folder sti', null=True)
    alias = models.CharField(max_length=64, verbose_name='Drevbogstav', null=True)

    # Run error messages
    MOUNT_FAILED = (
        "Scanneren kunne ikke startes," +
        " fordi netværksdrev ikke kunne monteres"
    )

    @property
    def root_url(self):
        """Return the root url of the domain."""
        url = self.url.replace('*.', '')
        return url

    def check_mountpoint(self):
        """Checks if networkdrive is already mounted."""

        if not self.mountpath or not os.path.isdir(self.mountpath):
            self.set_mount_path()

        response = call(['mountpoint', self.mountpath])
        return response

    def set_mount_path(self):
        if not os.path.isdir(settings.NETWORKDRIVE_TMP_PREFIX):
            os.makedirs(settings.NETWORKDRIVE_TMP_PREFIX)

        tempdir = tempfile.mkdtemp(dir=settings.NETWORKDRIVE_TMP_PREFIX)
        self.mountpath = tempdir
        self.save()

    def smb_mount(self):
        """Mounts networkdrive if not already mounted."""

        if not self.check_mountpoint():
            logger.info('{} is already a mount point.'.format(self.mountpath))
            return True

        # Make only one scanner able to scan mounted file directory.
        # Scrapy locks the files while reading, so it is not possible to have two scan jobs
        # running at the same time on the same mount point.

        command = ['sudo', 'mount', '-t', 'cifs',
                self.root_url, self.mountpath, '-o']

        optarg = 'iocharset=utf8'
        if settings.PRODUCTION_MODE:
            # Mount as apache user (www-data). It will always have uid 33
            optarg += ',uid=33,gid=33'
        if self.authentication.username:
            optarg += ',username=' + self.authentication.username
        if self.authentication.ciphertext:
            password = self.authentication.get_password()
            optarg += ',password=' + password
        if self.authentication.domain:
            optarg += ',domain=' + self.authentication.domain
        command.append(optarg)

        response = call(command)

        if response:
            logger.error('Mount failed: {0}'.format(response))
            return False

        logger.info('{} is mounted.'.format(self.mountpath))

        return True

    def smb_umount(self):
        """Unmounts networkdrive if mounted."""
        if not self.check_mountpoint():
            call(['sudo', 'umount', '-l', self.mountpath])
            call(['sudo', 'umount', '-f', self.mountpath])
            logger.info('{} is unmounted.'.format(self.mountpath))

    def __str__(self):
        """Return the URL for the domain."""
        return self.url

    class Meta:
        db_table = 'os2webscanner_filedomain'
