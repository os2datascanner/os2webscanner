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
from django.conf import settings
from django.core.mail import EmailMessage
from django.template import loader, Context

import models


def notify_user(scan):
    """Notify user about completed scan - including success and failure."""
    template = 'os2webscanner/email/scan_report.html'

    t = loader.get_template(template)

    subject = "Scanning afsluttet: {0}".format(scan.status_text)
    to_address = scan.scanner.organization.contact_email
    if not to_address:
        to_address = settings.ADMIN_EMAIL
    matches = models.Match.objects.filter(scan=scan).count()
    critical = models.Match.objects.filter(
        scan=scan,
        sensitivity=models.Sensitivity.HIGH
    ).count()

    c = Context({'scan': scan, 'domain': settings.SITE_URL, 'matches': matches,
                 'critical': critical})

    try:
        body = t.render(c)
        message = EmailMessage(subject, body, settings.ADMIN_EMAIL,
                               [to_address, ])
        message.send()
        print "Mail sendt til", to_address
    except Exception as e:
        # TODO: Handle this properly
        raise
