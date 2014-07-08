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
                               [to_address,])
        message.send()
        print "Mail sendt til", to_address
    except Exception as e:
        # TODO: Handle this properly
        raise
